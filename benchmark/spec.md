# Benchmark 规范：从建模 Prompt 到 `.scadpkg`

## 1. 评测对象和不可绕过的边界

一次 benchmark run 的输入只有一份 Prompt、固定版本的 SimpleCADAPI/CADIR 环境和一个空的工作目录。Agent 的交付物只有一个由本次源代码 capture 得到的 `.scadpkg`；预先放入的 `.scadpkg`、MJCF、mesh、验证报告和 verifier 都不属于输入。固定 KinCheckAPI verifier 由评测端私下运行，不出现在 Agent 的 Prompt、工作目录或操作流程中。

评测器固定以下事实：

1. Agent 可以选择建模 API 的合法调用、文件拆分和实现顺序，但只能交付 `.scadpkg`，不能交付或修改评测端 verifier。
2. `.scadpkg` 必须由本次运行的可编辑源 capture 得到；不能手工编辑 package 内的 JSON、BREP、mesh 或 mapping 来修正结果。
3. 评测端从 `.scadpkg` 独立导出仿真输入，再运行固定 verifier。Agent 不需要知道 verifier 如何采样、如何选 pair 或使用哪些内部检查。
4. Agent 只需在生成失败时修复自己的 CAD 源；不得通过降低几何间隙、删除组件、隐去连接关系或伪造 package 数据来“通过”。

评测端记录 Prompt hash、Agent/model、SimpleCADAPI/CADIR/KinCheckAPI 版本、Python 版本、构建命令、耗时、stdout/stderr、最终 package hash 和 verifier JSON。运行前清空构建缓存或明确记录缓存状态；第一次冷运行和后续暖运行不能混为一个性能分数。

## 2. Prompt 的固定结构

每份 Prompt 必须按下面顺序书写。Prompt 描述的是目标产品和目标工况，不描述 verifier 的函数、阈值、采样算法、pair 列表或报告字段。

### 2.1 第一部分：组件契约表

第一张表必须恰好有三列，列名固定为：

| Part/Component name | Naming | Geometry description |
| --- | --- | --- |
| 人类可读的零件或组件名 | 稳定的 definition/component/connector/interface 名称 | 尺寸、坐标、材料密度、形状、孔、倒角、轴向层、配合间隙和实体连接 |

表中每一行代表一个物理零件或一个明确的 occurrence，不代表“一个概念”。重复零件必须逐行列出，或在 `Naming` 中给出明确的 occurrence 列表及数量；不能只写“若干螺栓”。Geometry description 必须能从 CAD 产物核对，而不是只写“像一根连杆”。

### 2.2 Naming 规范

命名直接采用现有四连杆的方式：assembly 使用一个 `snake_case` 根名；part definition 使用角色名；单实例 component 使用角色名；重复 occurrence 使用 `pin_a`、`pin_b` 这类有语义的实例名；connector 使用 `pivot_a`、`pivot_b`、`axis`、`mount` 这类功能名。所有公开 ID 使用 ASCII 小写 `snake_case`，不使用空格、中文、随机 hash 或位置坐标作为唯一命名。

| 对象 | 推荐格式 | 规则 |
| --- | --- | --- |
| Assembly | `guided_four_bar_actuator` | 整个 package 只一个根 ID |
| Part definition | `base`、`crank`、`coupler`、`rocker`、`ground_pin`、`link_pin`、`guard` | 角色名描述可复用实体和材料；不包含 occurrence 位姿 |
| Component/occurrence | 单件使用 `base`、`crank`、`coupler`；重复件使用 `pin_a`、`pin_b`、`pin_c`、`pin_d` | 每个实体实例唯一；definition 相同的 occurrence 仍逐个保留 |
| Connector | `pivot_a`、`pivot_b`、`pivot_d`、`axis`、`mount`、`guard_mount` | 同一 Part 内唯一；原点在真实轴线/安装面，轴向写入 Prompt |
| Joint/constraint | `crank_to_ground`、`coupler_to_crank`、`coupler_to_rocker`、`rocker_to_ground`、`guard_to_base`、`pin_*_fixed` | 类型、两端 connector、方向和限位都可反查；闭环关节不能匿名 |
| Interface/tag | 需要面级加载或功能接触时使用 `interface.<function>` | 绑定真实 face/region；不能凭外观猜选面 |

命名表还必须说明哪些对象是 `ground`、哪些固定到 host link、哪些是运动 body、哪些是功能接触面。定义 ID 相同不代表实例可以合并：`ground_pin` 的 `pin_a` 和 `pin_d` 必须各自保留。

**Verifier-facing Name Registry 是必填项。** 每份 Prompt 必须逐字列出评测端会引用的完整名称，不能让 Agent 自由派生：

```text
assembly_id: <exact>
root_component_id: <exact>
definition_ids: <exact list>
occurrence/component_ids: <exact list>
connector_ids_by_part: <exact mapping>
fixed_constraint_ids: <exact list>
revolute/prismatic joint_ids: <exact list>
closure_joint_id: <exact>
public_connector_ids: <exact list>
material_ids and density_unit: <exact values>
```

对于现有四连杆，必须使用：`guided_four_bar_actuator`；`base`、`crank`、`coupler`、`rocker`、`ground_pin`、`link_pin`、`guard`；occurrence `pin_a`、`pin_b`、`pin_c`、`pin_d`；fixed constraints `guard_to_base`、`pin_a_fixed`、`pin_b_fixed`、`pin_c_fixed`、`pin_d_fixed`；revolute joints `crank_to_ground`、`coupler_to_crank`、`rocker_to_ground`；closure joint `coupler_to_rocker`；public connector `crank_input_axis`。Prompt 中出现的名称必须和 package assembly graph 完全一致，不能使用 `base_crank`、`crank_coupler` 等替代名。

**材料单位也是硬契约。** 所有 Prompt 必须明确写 `density_unit`，只允许 `kg/m3`、`kg/m^3`、`kg/mm3` 或 `kg/mm^3`；推荐 CADIR 旧有示例使用 `kg/mm^3`。`g/cm3` 等其他单位必须在 Prompt 层转换后再交付，不能把单位选择留给 Agent 猜测。

### 2.3 第二部分：工况文本

表格后用文本冻结工况，至少按以下顺序描述：

1. **单位和坐标**：CAD 长度、角度、时间、世界原点、右手系、重力方向、轴正方向。
2. **拓扑和支承**：ground、组件连接、joint 类型、连接器两端、闭环关系、固定硬件和不能悬空的部件。
3. **初始状态**：初始姿态、零位、可动范围、装配间隙、允许的功能接触和必须避让的部件。
4. **工程运动要求**：用工程语言写输入与目标，例如“曲柄以 600 rpm 匀速旋转，滑块往复行程 100 mm”“输入轴与输出轴传动比 2:1”“摇杆摆角 −20° 到 45°”。如果需要启停，给出启动时间、保持时间、停止时间或加速度边界。
5. **目标安全要求**：例如运动全程无非预期干涉、导轨不脱离、护罩保持间隙、所有零件通过真实连接固定到基座。只描述要达到的目标，不写如何调用 verifier。

不要只写“平稳运动”“不能碰撞”“满足传动比”。必须给数值、方向、单位和适用时间范围。传动比要说明输入/输出对象、正负方向和单位；闭环机构要说明连接拓扑和目标运动，不要把输出位置逐采样硬编码成答案。

## 3. Agent 唯一交付物

Agent 最终只提交一个可读的 canonical package：

```text
<output>/<assembly>.scadpkg
```

源文件遵守 SimpleCADAPI skill 的“一 part 一文件、一个 assembly 文件、显式 feature boundary、显式 connector、增量 QL 验证、capture `.scadpkg`”规则。每个实体必须是有效单 solid，孔和空腔必须由真实布尔特征产生；不能用贴图、空壳、中心线或包围盒冒充实体。材料至少给出有效 density 和 density_unit。

`.scadpkg` 内的 assembly graph 必须能回答：每个 definition 对应哪些 occurrence；每个 occurrence 属于哪个 host/group；哪个 component grounded；每个 joint 的两端 connector；每个实体的 source revision/hash。package 缺失、重复或与 Prompt 命名不一致时，评测端判定产物无效。

## 4. 评测端私有验证

评测端在 Agent 交付 `.scadpkg` 后，私下完成导出并运行固定 verifier。Agent 不需要看到入口、命令或实现。评测端至少执行：

- 从 `scene.xml` + `scene.mapping.json` 调用 `convert_mjcf()`，再运行 `validate_assembly()` 与 `validate_topology()`；
- 按 Prompt 创建固定的 Scenario，运行 `solve_motion()`，检查 completed 状态、采样完整性和闭环/方程 residual；
- 检查 driver tracking、joint limits、轨迹范围和结果 scope；
- 对要求的全部 component/group pair 执行 sampled interference、minimum clearance 和 continuous interference。revolute/fixed 关系没有自动免检权；允许的功能接触必须单独列出；
- 使用同一次 CAD 导出的 leaf `collision_meshes` 检查组内 hardware/guard/pin；不能只检查合并后的一个 group mesh；
- 检查每个非 ground occurrence 有到 ground 的实际连接链，且不依靠悬空的视觉标记；
- 运行至少一个故意失败的 negative control，确认 verifier 能发现几何或运动错误；
- 保存每项 `passed`、`status`、`operation`、`object_ids`、时间/范围、实际值、期望值、单位、source path 和修复建议。

评测端不能读取 Agent 的 requirements 或源代码内部变量来替 Agent 证明命题。几何命题从 `.scadpkg` 独立导出的 mesh/BREP 重新测量，运动命题从实际 MotionResult 重新检查，不能接受 Agent 自己写入的 `verification.json` 作为通过证据。

## 5. 评分和判定

这是硬门槛 benchmark，先判是否可复现，再判结果是否正确：

| 阶段 | 通过条件 | 失败含义 |
| --- | --- | --- |
| Prompt 合同 | 三列表格、确定 ID、完整工程工况数值 | Agent 没有把目标写成可建模的结构化契约 |
| CAD 构建 | `.scadpkg` capture 成功、单 solid/材料/connector 完整 | 模型不是可复现的参数化产物 |
| 独立仿真 | 评测端固定 verifier 的硬检查通过，negative control 能被发现 | 模型不满足工况或几何安全目标 |
| 产物追溯 | package 内 definition、occurrence、joint、connector 和 source hash 完整 | package 不能稳定转换和复核 |

默认报告 `hard_pass` 只有在上述全部通过时为 true。可以另外记录 `build_time_s`、`verify_time_s`、首次/重复运行和 token/call 数，但性能不能抵消几何、拓扑或运动失败。若 Agent 改动固定 verifier、删掉检查、修改 threshold、把结果写成静态 JSON 或把异常吞掉，直接记为 `protocol_violation`。

## 6. 四连杆固定命名和评测映射

现有四连杆的 verifier 使用固定 ID：根 `node/guided_four_bar_actuator`，运动组 `crank`、`coupler`、`rocker`，关节 `crank_to_ground`、`coupler_to_crank`、`rocker_to_ground`，并通过闭环 mapping 找到 `coupler_to_rocker`。因此 benchmark prompt 必须要求 Agent 生成这些兼容 ID，不能让每次 Agent 自由改名后再修改 verifier。

评测端的私有连接路径是：

```text
source/guided_four_bar_actuator.cadir.py
  → out/guided_four_bar_actuator.scadpkg
  → source/export_mjcf.py
  → model/scene.xml + scene.mapping.json + meshes/ + collision_meshes/
  → verification/verify.py
  → convert_mjcf() → Scenario → solve_motion() → checks → JSON/exit code
```

该流程验证的是运动学和几何安全，不声称结构强度、疲劳、接触力或动力学。后续动力学 benchmark 必须在同一个命名和 mapping 之上增加物性 manifest 与绑定的 request/result，不能重新发明一套对象 ID。
