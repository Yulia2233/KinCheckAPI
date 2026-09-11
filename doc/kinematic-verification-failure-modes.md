# CADIR 装配体运动学验证风险矩阵

本文列出从 CADIR 产出到 KinCheckAPI 给出运动学结论的常见失败方式。它既覆盖会抛出结构化错误的输入问题，也覆盖“程序能跑完、但结论不可信”的语义问题。

其中一组可直接运行的实测触发脚本和返回记录见 [`fail/`](../fail/README.md) 与 [`fail/FAILURE_CASES.md`](../fail/FAILURE_CASES.md)。

v0.5.0 起，所有受控错误和公开验证结果只有一种 Agent 正文。直接
`print(error)` 或 `print(result)`；需要严格失败时调用 `result.raise_if_failed()`。
机器记录使用 `to_dict()`，失败案例另在顶层保存同源 `agent_output`。不要根据
`issues`、events 或 last valid result 手工拼接第二套错误文字。

## 如何使用

验证时先判断失败属于哪一类：

| 类别 | 含义 | Agent 的处理 |
| --- | --- | --- |
| 输入错误 | CADIR 文件、目录、命名或格式不满足转换契约 | 停止转换，报告路径、字段和修复动作 |
| 映射错误 | XML、mapping、source ID 或 AssemblyModel 对不上 | 不猜名称，不自动补对象，修复 CADIR 导出或 mapping |
| 装配/拓扑错误 | 组件、joint、closure、coupling、ground 关系不自洽 | 不创建有效工况，先修装配模型 |
| 场景错误 | 初始状态、驱动、时长、采样或结果请求不合法 | 修正 Scenario 后重新验证 |
| 求解失败 | 后端无法编译、无法收敛或只返回部分轨迹 | 保存结构化诊断；`partial` 永远不是通过 |
| 验收失败 | 运动完整，但残差、限位、传动、轨迹或几何要求不满足 | 结论为失败，并指出实际证据 |
| 能力不可用 | 当前 backend、关节类型或几何依赖不支持 | 结论为未验证/能力缺失，不得改成通过 |
| 交付错误 | JSON、`.kincheck`、网格或验证元数据不完整 | 不交付结果包，先做 round-trip 校验 |

## 通过结论的共同前提

任何声称“通过”的检查都必须同时满足：

1. 输入和参数为有限值，范围合法；
2. 装配和 Scenario 预检通过；
3. `MotionResult.status` 为 `completed` 或 `completed_with_warnings`，不是 `partial`；
4. 存在实际运动采样、实际检查对象和实际测量；
5. 没有未处理的 error 级 issue；
6. 证据值满足用户给出的阈值和时间范围；
7. 检查范围、排除项和名称映射与用户意图一致。

`completed` 只说明求解完成，不等于运动学要求通过；`failed` 是一次已经执行的检查结果；`capability_failed`、`partial` 和零样本都不能当作通过。

## 1. CADIR MJCF 产出、文件和映射不完整

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 1 | CADIR 没有生成 MJCF XML | 找不到 `.xml`；`KINCHECK-MJCF-FILE-MISSING` | 检查 XML 路径和文件大小 | 重新从同一 CADIR 版本导出 |
| 2 | CADIR 没有生成 mapping JSON | XML 存在但 mapping 不存在；`KINCHECK-MJCF-FILE-MISSING` | 检查 mapping 路径和 JSON 可读性 | 重新导出 XML + mapping，不手写半份 mapping |
| 3 | XML、mapping、mesh 来自不同导出批次 | model 名、source ID、mesh 数量互相对不上 | 比较根模型 ID、哈希、导出时间和 source map | 使用同一批次产物 |
| 4 | 只复制了 XML，没有复制 mesh 目录 | 转换失败或 clearance 找不到网格 | 检查 XML mesh file 引用和 `asset_root` | 一起复制完整资产目录 |
| 5 | 只复制了部分 mesh | 个别 component 无 Part asset；`KINCHECK-MJCF-ASSET-MISSING` | 对照 XML geom/mesh 与 asset 目录 | 补齐所有 rigid group 的 mesh |
| 6 | XML 根缺少 `model` 属性 | 转换失败；`KINCHECK-MJCF-MODEL-MISSING` | 检查根元素是否有非空 `model` | 重新导出并设置 `model=root_definition_id` |
| 7 | XML `model` 与 mapping `root_definition_id` 不一致 | 转换失败；`KINCHECK-MJCF-MAPPING-INVALID` | 直接比较两个字段 | 使用同一批次 XML 和 mapping |
| 8 | mapping schema 版本不支持 | `KINCHECK-MJCF-MAPPING-INVALID` | 查看 mapping 的 schema/version 字段 | 使用兼容 exporter 或明确适配器 |
| 9 | XML、mapping 或 mesh 路径逃出 `asset_root` | `KINCHECK-MJCF-PATH-ESCAPES-ROOT` | 规范化路径后检查是否仍在根目录下 | 拒绝该产物并修复导出路径 |
| 10 | mapping 指向不存在的 mesh | `KINCHECK-MJCF-ASSET-MISSING` | 对照 geom mesh 引用和 mesh 目录 | 补齐同批次 mesh 资产 |
| 11 | mapping 中必需字段缺失 | `KINCHECK-MJCF-MAPPING-INVALID` | 查看结构化错误中的字段证据 | 重新导出 mapping，不手写半份 mapping |
| 12 | XML joint/equality 引用未知对象 | `KINCHECK-MJCF-MAPPING-INVALID` | 对照 XML 名称、mapping source ID 和 source map | 重新导出同批次 XML + mapping |
| 13 | 单位或数值字段缺失、非有限或不支持 | `KINCHECK-MJCF-MAPPING-INVALID`、`KINCHECK-MJCF-XML-INVALID` | 检查单位、axis、位置和 phase 数值 | 明确单位后重新导出，禁止猜单位 |
| 14 | XML 结构不能被 内置物理后端 解析 | `KINCHECK-MJCF-XML-INVALID` | 用 内置物理后端/MjSpec 重新加载并读取解析证据 | 修复 XML 后重新导出 |
| 15 | CADIR 导出被中途终止，只有半个目录 | 文件存在但 XML 截断或 mesh 数量不全 | 比较导出清单、文件大小和修改时间 | 清理该批次并重新完整导出 |
| 17 | 文件名包含临时后缀或缓存版本 | 验证环境读取了旧 `.tmp`、`.bak` 或缓存文件 | 列出目录并检查修改时间/哈希 | 只使用明确的正式导出路径 |
| 18 | 产物被覆盖后 source map 仍是旧版本 | 转换能成功，但对象追溯错位 | 比较 XML、mapping、source map 哈希 | 同步更新或重新生成 source map |

## 2. 命名、映射和 source ID 错误

这是“验证环境里 CADIR 产出了东西，但不是这个命名”的典型来源。文件存在并不表示它是当前模型。

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 19 | XML `model` 与 mapping `root_definition_id` 不同 | `KINCHECK-MJCF-MAPPING-INVALID` | 直接比较两个字段 | 从同一 CADIR 导出重新生成 |
| 20 | mapping 引用旧 XML 名称 | `KINCHECK-MJCF-NAME-UNRESOLVED` | 检查 body/joint/site/equality 名称是否在 XML 存在 | 更新 mapping，不按相似名称猜测 |
| 21 | CADIR 重命名了 body，mapping 未更新 | 某组件消失或转换失败 | 对照 XML body 与 mapping group | 同批次重新导出 |
| 22 | CADIR 重命名了 joint，Scenario 仍使用旧 ID | `SCENARIO-JOINT-NOT-FOUND` | 比较 AssemblyModel joint IDs 和 Scenario driver IDs | 使用转换后的稳定 ID |
| 23 | 显示名相同但 source ID 不同 | Agent 选错组件或 joint | 读取 source map 和稳定 ID | 业务脚本只使用稳定 ID |
| 24 | source ID 为空 | 对象被静默跳过或 source map 不完整 | 检查 mapping 中 public connector/group/joint ID | 结构化失败，回 CADIR 补 ID |
| 25 | source ID 重复 | `KINCHECK-MJCF-MAPPING-INVALID` 或映射冲突 | 对所有 component/joint/site/equality ID 去重 | 修复 CADIR ID 生成器 |
| 26 | source ID 含前后空格、大小写变化或非法字符 | 查找同名对象失败 | 原样打印 repr 和 source map | 统一命名规则后重新导出 |
| 27 | 使用了文件名推断 object ID | 能加载文件但检查了错误的组件 | 对照 `assembly.components`、`joints` 的实际 ID | 禁止从显示文件名推断 ID |
| 28 | 只改了 XML 名称，没有改 mapping | 转换失败或映射到旧对象 | 双向比较 XML 记录和 mapping | 同时更新二者 |
| 29 | 只改了 mapping 名称，没有改 XML | `NAME-UNRESOLVED` | 检查 mapping 每个引用 | 重新导出 |
| 30 | mapping 少了 XML equality | 闭环数量少于 CADIR 设计 | 统计 XML `<equality>` 和 mapping closure/equality | 需要双向一一对应 |
| 31 | mapping 多了不存在的 equality | 转换失败或 closure 引用无效 | 对照 XML equality 索引 | 删除错误映射并重新导出 |
| 32 | equality 名称相同但 site1/site2 不同 | 闭环连错端点，可能仍能编译 | 比较 XML equality 的两个 site 和 source map | 逐字段交叉校验 |
| 33 | site endpoint 指向错误 body | 机构拓扑看似连通但运动方向错误 | 追踪 site 所属 body 和 connector source ID | 修复 CADIR 约束端点 |
| 34 | connector 方向/名称映射错位 | 目标 pose 或传动方向错误 | 读取 connector frame 和 source map | 重新导出并验证 frame |
| 35 | 验证环境加载了另一个同名模型 | 结果与当前 CADIR 预览不一致 | 打印绝对路径、文件哈希和 model ID | 禁止隐式搜索；使用绝对路径 |
| 36 | 测试脚本硬编码旧组件名 | 业务脚本报不存在或检查错误对象 | 检查脚本常量与当前 assembly IDs | 从转换结果生成/校验 ID 清单 |
| 37 | 只按数量判断转换成功 | 数量相同但对象语义不同 | 比较完整 ID 集合和关系图 | 使用集合、关系和 source map 验证 |
| 38 | source map 没有持久化 | 能验证但无法回到 CADIR 源对象 | 检查 source map 文件和哈希 | 作为结果附件写出 |

## 3. 几何、单位、姿态、轴和角度语义错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 39 | mm 被当成 m | 位移/间隙放大 1000 倍，机构几乎不动或穿透 | 比较 MJCF/mapping 单位与 AssemblyModel 数值 | 统一转换到 SI |
| 40 | degree 被当成 rad | 30 度被当成 30 rad，姿态完全异常 | 检查源导出约定和 range 数值 | 明确导出单位，不凭经验换算 |
| 41 | rad 被重复转换 | 角度缩小约 57.3 倍 | 检查转换器和 CADIR exporter 的单位责任 | 只在边界层做一次换算 |
| 42 | 滑动 joint 的范围按角度处理 | prismatic 行程错误 | 检查 joint type 和 range 单位 | revolute 用 rad，slide 用 m |
| 43 | MJCF joint axis 被丢弃 | 非 Z 轴 slide/revolute 沿 Z 运动但仍 completed | 比较 XML axis、Connector frame 和结果轨迹 | 保留 axis 并做轴向回归 |
| 44 | 轴向量为零或非有限 | `KINCHECK-MJCF-JOINT-AXIS-INVALID` | 检查 axis 三分量和范数 | 修复 CADIR joint axis |
| 45 | 轴方向符号反了 | 输入正转时输出反转；传动比方向错 | 做正向小步运动并比较符号 | 修复 axis/frame 或明确 ratio 符号 |
| 46 | 局部轴和世界轴混淆 | 初始姿态正确，旋转后轨迹偏离 | 检查 joint pose、body pose、connector frame | 按局部坐标系转换 |
| 47 | 四元数分量顺序错 | 物体翻转、闭环方向残差大 | 检查 xyzw/wxyz 约定 | 统一 Pose 约定并做 round-trip |
| 48 | 初始 body pose 与 joint qpos 不一致 | 第一帧闭环残差大 | 对比 XML 初始 pose、range、initial state | 修复 CADIR 初始装配姿态 |
| 49 | 初始 pose 已含 coupling phase，但 phase 又写入 | 第一帧方程残差非零或 partial | 检查初始 pose 与 coupling phase 的责任 | 只保留一次 phase 贡献 |
| 50 | closure 只约束点重合，没有轴对齐 | 平面样例正常，空间机构发生扭转 | 检查 closure metadata 和 axis alignment | 对 revolute closure 启用轴对齐语义 |
| 51 | body 的缩放或 mesh scale 错 | 渲染大小与运动尺度不一致 | 检查 STL `scale_to_m`、Part metadata | 修复网格单位和缩放 |
| 52 | mesh 原点/坐标系错误 | 干涉位置不对，运动轨迹看似正确 | 对照 CADIR 预览和 STL 包围盒 | 重新导出 mesh pose |
| 53 | mesh 法向或三角网格退化 | FCL 查询失败或结果异常 | 检查 mesh 合法性和非零面积三角形 | 修复/重导出网格 |
| 54 | 只转换了第一个 mesh group | 四连杆某些杆件缺几何，干涉漏检 | 对照每个 rigid group 的 mesh 数 | 合并/保留完整 mesh 集合 |
| 55 | 关节 range 上下限反了或跨度为零 | 场景驱动超限或求解无法动 | 检查 lower/upper 和 joint type | 修复 CADIR 限位语义 |
| 56 | 容差单位和测量单位不一致 | 错误通过或错误失败 | 在报告中同时打印值和单位 | 所有公开阈值显式带 SI 单位 |

## 4. AssemblyModel、拓扑和约束关系错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 57 | 没有 ground | 拓扑不定或求解器编译失败 | 检查 `assembly.grounds` | 在 CADIR 明确固定基座 |
| 58 | ground 指向不存在 component | assembly/topology validation failed | 检查 ground ID | 修复 grounding 引用 |
| 59 | ground 选错 component | 机构整体漂移或运动参考错 | 对照 CADIR 固定件 | 修复 CADIR ground 约束 |
| 60 | component ID 重复 | Assembly validation failed | 对组件 ID 去重 | 修复源模型 |
| 61 | component 引用的 Part 不存在 | 组件无几何或无法编译 | 检查 part/component 关联 | 补齐 Part |
| 62 | joint endpoint component 不存在 | `JOINT-NOT-FOUND` 或 assembly error | 检查 joint 两端引用 | 修复连接关系 |
| 63 | connector 不存在或 connector_id 错 | 场景/目标/closure 找不到 connector | 对照 component connector 列表 | 修复 endpoint 和 source map |
| 64 | joint 类型不被当前 backend 支持 | capability error 或未实现 | 查看 joint type 和 backend capability | 改用支持的单自由度建模或明确未验证 |
| 65 | revolute/slide 方向和预期不符 | 能动但输出方向错 | 比较 axis、正方向小步响应 | 修复轴/坐标系 |
| 66 | joint 被错误固定/锁定 | 自由度比预期少，机构不动 | 查看 locked joints、fixed members | 删除错误固定或在报告说明 |
| 67 | closure 端点缺失 | `KINCHECK-CLOSURE-ENDPOINT-MISSING` | 检查 closure endpoint IDs | 修复 CADIR closure |
| 68 | closure 连接了错误的两个 connector | 残差大、求解 partial 或运动形态错误 | 比较 source equality site1/site2 | 修正 equality/site 映射 |
| 69 | closure 初始姿态不匹配 | `KINCHECK-CLOSURE-INITIAL-POSE-MISMATCH` | 运行初始姿态/closure residual | 修复初始装配姿态 |
| 70 | closure 约束过多或重复 | mobility 断开、零自由度或不收敛 | 比较约束数量、rank 和 CADIR 设计 | 删除重复约束或修源模型 |
| 71 | closure 约束过少 | 机构自由度异常增加，杆件可穿过 | 对比 CADIR equality 清单 | 补齐未映射 equality |
| 72 | coupling endpoint 类型不匹配 | `KINCHECK-KIN-COUPLING-ENDPOINT-TYPE-MISMATCH` | 检查转动/滑动 endpoint 类型 | 修复传动建模 |
| 73 | coupling radius、teeth 或 pitch 参数非法 | `COUPLING-RADIUS-INVALID`、`RATIO-TEETH-INVALID` | 检查参数是否有限且为正 | 修复 CADIR 参数 |
| 74 | coupling ratio 配置不被支持 | `KINCHECK-RATIO-CONFIGURATION-UNSUPPORTED` | 检查 stage/ratio 类型 | 降级为支持的表达或报告能力缺失 |
| 75 | coupling phase 被重复或漏掉 | 方程残差稳定偏移 | 对照初始 pose 和 phase source | 明确 phase 的唯一来源 |
| 76 | collision exclusion 把真正应检查的 pair 排除了 | 干涉“通过”但漏检 | 列出 exclusion 与用户检查 pair | 将排除项作为显式策略审阅 |
| 77 | collision exclusion pair 长度不是 2 | 裸崩溃或结构化 `COMPONENT-PAIR-INVALID` | 先检查每个 pair 长度 | 修复映射，不访问 `pair[1]` 后再校验 |
| 78 | disconnected component 未被发现 | 某杆件完全不受约束但求解仍有结果 | 检查 kinematic tree 和 mobility | 修复拓扑，不能只看 completed |
| 79 | 机构闭环方向与 CADIR 设计方向相反 | 运动形态“能跑”但不是目标机构 | 比较输入正向和目标输出方向 | 做方向回归和 source ID 对照 |
| 80 | AssemblyModel 与 MotionResult 不属于同一装配 | `KINCHECK-CHECK-ASSEMBLY-MISMATCH` | 比较 assembly/scenario IDs、hash/metadata | 同一装配重新求解 |

## 5. Scenario、驱动和初始条件错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 81 | 没有设置正的运行时长 | 空结果或 `SCENARIO-DURATION-INVALID` | 查看 `duration_s` | 设置覆盖需求的时长 |
| 82 | 采样周期为零、负数或非有限 | `SCENARIO-SAMPLE-PERIOD-INVALID` | 检查 `period_s` | 设置有限正采样周期 |
| 83 | 采样周期太大 | `SCENARIO-SAMPLE-PERIOD-TOO-LARGE` 或只得到很少样本 | 比较 duration/period 和实际 sample count | 减小周期并重新求解 |
| 84 | 驱动 start/end 反向或越界 | `SCENARIO-DRIVER-TIME-INVALID`、`OUTSIDE-RANGE` | 检查时间点和 Scenario window | 修复 driver 时间 |
| 85 | 速度、位置或 profile 含 NaN/无穷 | `DRIVER-VALUE-INVALID`、`PROFILE-INVALID` | 对 profile 每个点做 finite 检查 | 删除非法点并重新生成 |
| 86 | 同一 joint 同时被冲突的 position/speed driver 驱动 | `SCENARIO-DRIVER-CONFLICT` | 列出该 joint 的全部 driver | 保留一个明确输入 |
| 87 | 驱动了 fixed/locked joint | `SCENARIO-FIXED-JOINT-DRIVEN` | 检查 locked/fixed 与 driver ID | 取消锁定或更换驱动对象 |
| 88 | 初始位置超出 authored range | `SCENARIO-JOINT-LIMIT-VIOLATION` | 比较初始值和 joint limit | 修正初始姿态或范围 |
| 89 | 初始位置与闭环几何不一致 | `SCENARIO-INITIAL-STATE-INCONSISTENT` | 初始 solve + closure residual | 用 CADIR 正确装配姿态初始化 |
| 90 | 初始速度单位错误 | 第一帧运动过快/过慢，传动比失真 | 检查 rad/s 与 m/s | 修复单位 |
| 91 | 驱动了错误的 joint 名称 | `SCENARIO-JOINT-NOT-FOUND` | 比较当前 AssemblyModel joint IDs | 使用稳定 source ID |
| 92 | 没有请求输入/输出轨迹 | 检查 `TRAJECTORY-NOT-FOUND`、空结果 | 查看 result requests/scope | 在求解前请求目标轨迹 |
| 93 | component result scope 过窄 | 目标组件未记录，后续 pose/干涉无法检查 | 检查 `requested` 范围 | 请求所需组件或使用 `all` |
| 94 | 没开启 integration step，却要求后端细采样证据 | `INTEGRATION-SAMPLES-MISSING` | 查看 capture 设置和 metadata | 显式开启并记录代价 |
| 95 | 禁用了关键 closure/constraint | 结果比真实机构自由，误判通过 | 对比 disabled IDs 与原始装配 | 恢复约束；对照实验单独命名 |
| 96 | Scenario 引用另一 AssemblyModel | `SCENARIO-ASSEMBLY-MISMATCH` | 比较 scenario.assembly 和当前 assembly | 重新创建 Scenario |
| 97 | 把静态 smoke check 当成完整运动 | `completed` 但没有输入驱动或只有单点 | 检查 driver、duration、sample count | 明确结论只能是静态姿态通过 |
| 98 | 驱动时长短于用户要求时间窗 | 末帧正常但后段未验证 | 比较 run duration 与验收窗口 | 延长 Scenario |

## 6. 求解器、MotionResult 和完整性错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 99 | 内置物理后端/backend 不可用 | `KINCHECK-BACKEND-UNAVAILABLE`、`KIN-BACKEND-CAPABILITY` | 检查依赖和 backend 状态 | 标记能力缺失，不判通过 |
| 100 | 后端编译失败 | `KINCHECK-KIN-COMPILE-FAILED` | 读取原始 cause、模型 ID 和 XML 诊断 | 修模型/依赖，保留结构化错误 |
| 101 | 求解器在首帧就失败 | `KIN-SOLVE-FAILED`、`KIN-EMPTY-RESULT` | 使用 `try_solve_motion()` 检查首帧残差 | 修初始姿态、闭环或驱动 |
| 102 | 求解中途不收敛 | 返回 `partial` 或 `KIN-SOLVE-FAILED` | 记录 first failure time、last valid frame | 结论为未完成，不能通过 |
| 103 | 失败前缀轨迹被误当完整轨迹 | 轨迹有数据且检查返回 passed | 检查 `MotionResult.status` 和 end time | 统一拒绝 partial |
| 104 | `completed_with_warnings` 被忽略 | 求解完成但 backend warning 未审阅 | 读取 `issues`/warnings/backend info | 逐条解释 warning |
| 105 | 结果没有 sample times | `KINCHECK-KIN-EMPTY-RESULT` 或检查无样本 | 检查 `sample_times_s` | 不能判通过 |
| 106 | 结果时间轴不单调/不覆盖 Scenario | 轨迹查询错误或窗口检查失败 | 检查 times、start/end、sample period | 修复后端或场景 |
| 107 | joint trajectory 缺失 | `KINCHECK-RESULT-TRAJECTORY-MISSING` | 对照请求和 MotionResult trajectories | 重新请求并求解 |
| 108 | component/connector trajectory 缺失 | pose/trajectory/clearance 无法执行 | 检查 result scope 和 IDs | 扩大记录范围 |
| 109 | closure residual 数量为零 | 检查“没有残差”而通过 | 检查是否真的存在 closure/equation samples | 零样本失败或报告未检查 |
| 110 | 残差超过容差 | `CLOSURE-RESIDUAL-EXCEEDED`、`CONSTRAINT-*RESIDUAL-EXCEEDED` | 读取最大残差、时间和对象 ID | 结论为验收失败 |
| 111 | 后端只输出最后一帧 | 静态 pose 看起来正确，轨迹无法验证 | 检查 sample count 和时间序列长度 | 增加采样和结果请求 |
| 112 | 结果被另一个 Scenario 覆盖 | JSON ID、driver 或 duration 对不上 | 比较 scenario_id、assembly_id 和 metadata | 重新求解并隔离输出路径 |
| 113 | 结果 JSON 手工删掉 issue/采样 | Viewer 可打开但证据不完整 | 对比原始运行日志和 JSON | 禁止手工篡改结果作为验收依据 |
| 114 | backend warning 被业务脚本吞掉 | 退出码 0、只打印 passed | 查看脚本是否调用 `assert_check_passed` | 失败时非零退出 |
| 115 | 运行时模型与 source map 不一致 | 可以求解但无法追溯到 CADIR | 比较 hashes、IDs 和 conversion metadata | 同批次重新转换/求解 |

## 7. 闭环、姿态和约束残差错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 116 | 两个 closure endpoint 位置不重合 | `CLOSURE-RESIDUAL-EXCEEDED` | 查看位置残差和 endpoint ID | 修初始姿态或 closure 几何 |
| 117 | revolute closure 轴方向不一致 | 点位置残差小但方向误差大/空间机构扭转 | 查看 axis alignment evidence | 在 CADIR 正确设置轴和 closure 语义 |
| 118 | closure equality 类型不支持 | `EQUATION-TYPE-INVALID`、`SEMANTICS-UNSUPPORTED` | 检查 equality type | 转为支持的闭环表达或报告能力缺失 |
| 119 | 约束方程残差超阈值 | `CONSTRAINT-EQUATION-RESIDUAL-EXCEEDED` | 查看 equation ID、最大残差和时间 | 修 phase、ratio、axis 或拓扑 |
| 120 | 约束检查传入了错误 constraint ID | `CHECK-CONSTRAINT-NOT-FOUND` | 对照 assembly closure/constraint IDs | 使用稳定 ID |
| 121 | 约束容差为 NaN/无穷/负数 | `CHECK-CONSTRAINT-TOLERANCE-INVALID` | finite + range 校验 | 提供有限非负容差 |
| 122 | 位置/方向残差单位混用 | 位置以 rad 比较或方向以 m 比较 | 检查参数名和报告 unit | position 用 m，orientation 用 rad |
| 123 | 只检查最后一帧而忽略中途峰值 | 末帧满足，途中闭环断开 | 检查 sampling scope 和 max residual over time | 采用完整时间窗口 |
| 124 | 关闭了 constraint 后仍称原模型通过 | 约束残差“通过”但模型已改 | 对比 disabled constraints | 分离诊断结果和原模型验收 |
| 125 | 初始姿态误差被求解器强行纠正 | 结果最终正常，但真实装配初态不对 | 比较初始 frame residual 和 input pose | 把初态校验作为独立门槛 |

## 8. 关节限位、姿态和轨迹验收错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 126 | joint 没有 authored limit | `CHECK-JOINT-LIMIT-NOT-AUTHORED` | 检查 limit 是否存在 | 报告“未建模”，不能安全通过 |
| 127 | 轨迹超出 joint range | `CHECK-JOINT-LIMIT-EXCEEDED` | 查看 joint、time、actual、expected | 验收失败或回 CADIR 修限位 |
| 128 | limit tolerance 非法 | `CHECK-JOINT-LIMIT-TOLERANCE-INVALID` | finite + non-negative 校验 | 修阈值 |
| 129 | 只检查位置，不检查 limit event | 轨迹看似正常但事件数超限 | 查看 `limit_events` | 把事件数作为明确验收条件 |
| 130 | 目标 component ID 不存在 | `POSE-TARGET-INVALID`、`TARGET-NOT-FOUND` | 检查 assembly IDs | 修目标映射 |
| 131 | 目标 Pose 为空或字段不完整 | `POSE-TARGET-EMPTY`、`POSE-TARGET-INVALID` | 检查位置、方向和 frame | 补齐目标 Pose |
| 132 | 目标坐标系错 | 数值误差小但相对错误 frame | 检查 target/reference frame | 明确 frame 后重算 |
| 133 | 位置目标满足、方向目标不满足 | `POSE-TARGET-MISMATCH` | 分开读取 position/orientation error | 分别设置 m/rad 容差 |
| 134 | 目标时间超出运动窗口 | `CHECK-TIME-WINDOW-INVALID` | 比较 target time 与 sample times | 扩大窗口或修改目标时间 |
| 135 | 轨迹数据缺失 | `TRAJECTORY-DATA-MISSING`、`TRAJECTORY-NOT-FOUND` | 检查 request 和 result | 重新求解并请求轨迹 |
| 136 | 轨迹位移范围错误 | `TRAJECTORY-POSITION-OUT-OF-RANGE` | 计算 min/max 与阈值 | 报告实际极值 |
| 137 | 轨迹速度/路径范围错误 | `TRAJECTORY-CONSTRAINT-EXCEEDED`、`PATH-LENGTH-OUT-OF-RANGE` | 检查速度、路径长度、时间 | 调整机构/驱动或判失败 |
| 138 | 轨迹阈值上下限反了 | `TRAJECTORY-BOUNDS-INVALID` | 检查 min <= max | 修验收参数 |
| 139 | 路径阈值非法 | `TRAJECTORY-PATH-LIMIT-INVALID` | 检查 finite/non-negative | 修验收参数 |
| 140 | 样本不足以证明轨迹 | 单点或极少点却返回无 issue | 检查 sample count 和时间跨度 | 增加采样并明确最小样本数 |

## 9. 滑动参数和传动比错误

这里的“滑动比错误”可能指滑动 joint 的位移比例，也可能指旋转-滑动、齿轮、皮带或齿条传动的比值；必须先确认具体语义。

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 141 | slide joint axis 错 | 滑块沿错误方向移动 | 比较 XML axis 与输出 displacement vector | 修 joint axis/frame |
| 142 | slide 行程单位错 | 期望 20 mm 却移动 20 m 或 0.02 mm | 检查 range、driver、结果单位 | 统一 m |
| 143 | 旋转-滑动 coupling endpoint 类型错误 | `COUPLING-ENDPOINT-TYPE-MISMATCH` | 检查 revolute/prismatic 角色 | 修 coupling 端点 |
| 144 | 传动 ratio 大小错误 | `RATIO-MISMATCH` | 用完整 joint trajectories 测实测 ratio | 修 ratio/半径/齿数 |
| 145 | ratio 正负号错误 | `RATIO-DIRECTION-MISMATCH` | 输入正向小步与输出符号 | 修 axis 或 coupling sign |
| 146 | ratio direction 参数非法 | `RATIO-DIRECTION-INVALID` | 检查 direction 枚举/值 | 使用支持值 |
| 147 | ratio 期望值 NaN/无穷/非法 | `RATIO-EXPECTED-INVALID` | finite + range 校验 | 修验收输入 |
| 148 | ratio tolerance 非法 | `RATIO-TOLERANCE-INVALID` | finite + non-negative 校验 | 修容差 |
| 149 | ratio 最小输入变化过小 | `RATIO-MINIMUM-INPUT-INVALID` 或测量噪声大 | 检查输入位移/角度变化 | 增大驱动幅度或报告不可测 |
| 150 | 输入输出轨迹没有时间重叠 | `RATIO-NO-TIME-OVERLAP` | 比较两条 trajectory 时间区间 | 重新请求同一时间窗口 |
| 151 | 输入或输出 joint trajectory 缺失 | `RATIO-TRAJECTORY-NOT-FOUND` | 检查 result requests | 重新求解并请求两个 joint |
| 152 | 实际样本不足 | `RATIO-INSUFFICIENT-SAMPLES` | 检查有效差分点数 | 增加采样/驱动幅度 |
| 153 | ratio measurement 不支持该 joint 类型 | `RATIO-MEASUREMENT-UNSUPPORTED` | 检查 joint type 和 backend capability | 报告未验证 |
| 154 | 多级传动 stage 数量不一致 | `RATIO-STAGE-COUNT-MISMATCH`、`STAGE-MISMATCH` | 对照 CADIR coupling stages | 修 source coupling |
| 155 | 固定构件没有 grounded | `RATIO-FIXED-MEMBER-NOT-GROUNDED` | 检查传动 reference member | 明确 ground |
| 156 | 齿数/半径关系错误 | `RATIO-TOOTH-RELATION-INVALID` | 根据 CADIR 参数独立计算 | 修建模参数 |
| 157 | coupling phase 非零但重复施加 | 初始 ratio 方程出现固定偏差 | 比较初始姿态、phase 和 equation residual | 归一化 phase |
| 158 | 传动比只看单帧位置 | 恰好通过但无法证明比例 | 检查有效时间样本和差分 | 进行完整窗口实测 |

## 10. 奇异性、可达性、工作空间错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 159 | Jacobian 首帧零秩/退化 | `KINCHECK-KIN-SINGULAR` | 检查首帧 rank 和对象 ID | 修初始姿态或机构拓扑 |
| 160 | 运动中接近奇异 | `KINCHECK-KIN-NEAR-SINGULAR` | 查看时间、condition/rank 阈值 | 报告风险，不要只说“能动” |
| 161 | 奇异性分析没有样本 | `KIN-SINGULARITY-NO-SAMPLES` | 检查 MotionResult 完整性 | 先生成足够轨迹 |
| 162 | 奇异性选项非法 | `KIN-SINGULARITY-OPTIONS-INVALID` | finite + range 校验 | 修分析参数 |
| 163 | 奇异性能力不可用 | `KIN-SINGULARITY-UNAVAILABLE` | 检查 backend/数据能力 | 标记未验证 |
| 164 | target component/connector 不存在 | `KIN-TARGET-NOT-FOUND` | 检查目标 ID | 修目标映射 |
| 165 | 目标在当前约束下不可行 | `KIN-TARGET-INFEASIBLE` | 读取最近姿态、残差和限制 | 修目标或机构 |
| 166 | 目标证据不完整 | `KIN-TARGET-EVIDENCE-INCOMPLETE` | 检查 sample、轨迹、frame | 增加请求和采样 |
| 167 | workspace 未提供 joint range | `WORKSPACE-RANGE-REQUIRED` | 检查每个采样 joint 的范围 | 明确 range |
| 168 | workspace 使用不支持的 joint | `WORKSPACE-JOINT-UNSUPPORTED` | 检查 joint type | 只分析支持类型 |
| 169 | workspace joint ID 错 | `WORKSPACE-JOINT-NOT-FOUND` | 对照 AssemblyModel | 修 ID |
| 170 | workspace 采样失败或被截断 | `WORKSPACE-SAMPLE-FAILED`、`SAMPLE-TRUNCATED` | 读取 sample issues/count | 报告覆盖率，不能当完整 workspace |

## 11. 干涉、最小间隙和运动包络错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 171 | 两个组件真实穿透 | `CLEARANCE-INTERFERENCE-DETECTED` | 查看 event time、pair、penetration depth | 验收失败，回 CADIR 修几何/行程 |
| 172 | 关节相邻件接触但未设置容差/排除 | 报告 false，用户不确定是否算干涉 | 查看 pair、penetration tolerance 和 exclusion | 明确“关节接触是否允许”的业务规则 |
| 173 | 最小间隙低于阈值 | `CLEARANCE-MINIMUM-BELOW-THRESHOLD` | 查看最小 signed clearance 和时间 | 增大间隙、改行程或判失败 |
| 174 | penetration tolerance 为负/NaN/无穷 | `CLEARANCE-PARAMETER-INVALID` | finite + non-negative 校验 | 修容差 |
| 175 | minimum allowed clearance 非法 | `CLEARANCE-PARAMETER-INVALID` | 检查单位和范围 | 修阈值 |
| 176 | component_pairs 显式为空 | `CLEARANCE-COMPONENT-PAIRS-EMPTY` | 检查调用参数 | 视为输入错误，不判通过 |
| 177 | component pair 长度不是 2 | `CLEARANCE-COMPONENT-PAIR-INVALID` | 检查 tuple 长度和 ID | 修 pair |
| 178 | pair 引用不存在 component | `COMPONENT-PAIR-NOT-FOUND` | 对照 assembly component IDs | 修组件范围 |
| 179 | pair 包含同一 component | 检查范围无意义或被拒绝 | 检查 pair 两端是否不同 | 修 pair |
| 180 | 未提供 pair 导致检查范围过大 | 计算很慢，或结果包含非目标件 | 查看默认范围和 metadata | 业务验收显式列 pair |
| 181 | 组件选择显式为空 | `CLEARANCE-COMPONENT-SELECTION-EMPTY` | 检查 component_ids | 报输入错误 |
| 182 | `component_ids=()` 被解释成全部组件 | 漏检/误检范围扩大 | 检查调用和报告 metadata | 禁止空选择 fallback |
| 183 | mesh 文件缺失 | `CLEARANCE-MESH-NOT-FOUND` | 检查 Part.asset_paths 和 asset_root | 补齐 STL |
| 184 | mesh 格式不被支持 | `CLEARANCE-MESH-INVALID` | 检查 STL 解析和三角面 | 重导出合法 STL |
| 185 | FCL backend 不可用 | `CLEARANCE-BACKEND-UNAVAILABLE` | 检查 python-fcl/版本 | 安装依赖或明确未验证 |
| 186 | FCL 查询异常 | `CLEARANCE-QUERY-FAILED`、`CONTAINMENT-QUERY-FAILED` | 保存 cause 和 pair/time | 修 mesh/backend，不吞异常 |
| 187 | 运动结果是 partial | `CLEARANCE-MOTION-RESULT-INCOMPLETE` | 检查 motion.status | 不能通过，最多分析失败前缀 |
| 188 | 运动结果没有 component trajectory | `CLEARANCE-TRAJECTORY-MISSING` | 检查 result scope | 重新请求组件轨迹 |
| 189 | 采样间隔太粗 | `CLEARANCE-SAMPLING-TOO-COARSE` | 比较 max sample period 和机构速度 | 减小 period 或启用 integration samples |
| 190 | integration samples 缺失/非法 | `CLEARANCE-INTEGRATION-SAMPLES-MISSING`、`INVALID` | 检查 capture metadata | 重新求解并捕获 |
| 191 | 几何采样时间窗口非法 | `CLEARANCE-TIME-WINDOW-INVALID` | 检查 start/end 与 result times | 修窗口 |
| 192 | motion envelope 为空 | `CLEARANCE-ENVELOPE-EMPTY` | 检查 component trajectory/sample count | 不能判无包络干涉 |
| 193 | envelope 输入失败 | `CLEARANCE-ENVELOPE-INPUT-FAILED` | 检查 mesh、pose、component ID | 修输入 |
| 194 | envelope 自身重叠 | `CLEARANCE-ENVELOPE-OVERLAP` | 查看 component/time evidence | 报告包络风险，不能判安全 |
| 195 | 只检查末帧干涉 | 途中发生碰撞但末帧分离 | 检查 sampling_scope | 使用完整 motion_result/integration samples |
| 196 | 只检查几何，不检查运动完整性 | partial 前缀“无碰撞” | 检查 clearance issues | 先过 motion completeness gate |
| 197 | collision exclusion 与验证目标冲突 | 应检查的 pair 被排除 | 对照 collision policy 和用户要求 | 让排除项显式、可审阅 |
| 198 | 网格与运动 pose 不属于同一版本 | 视图/干涉结果偏移 | 比较 asset hash 和 assembly source | 同批次导出 |

## 12. 检查编排和业务脚本错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 199 | `run_checks()` 没有传 `motion_result` | `CHECK-MOTION-RESULT-REQUIRED` | 检查 check type 所需输入 | 先求解并传入结果 |
| 200 | CheckSpec 类型名称拼错或不支持 | `CHECK-TYPE-UNSUPPORTED` | 对照支持的 CheckType | 修 check spec |
| 201 | 同一 check_id 重复 | `run_checks()` 抛重复 ID | 检查 spec IDs | 使用唯一稳定 ID |
| 202 | 业务脚本只打印 `report.passed` | 未来回归为 True 仍退出 0 | 审查脚本是否 assert/非零退出 | 使用 `assert_check_passed()` |
| 203 | 预期失败案例没有断言失败 | 失败模型回归成通过无人发现 | 检查 verify 脚本 | 明确 expected status/code |
| 204 | 只断言异常，不断言错误码 | 抛了错误但根因变了仍通过测试 | 检查 code/object_ids | 断言结构化 code 和关键对象 |
| 205 | 检查范围默认化 | 业务脚本没有列出目标 joint/pair | 检查 parameters 和报告 metadata | 所有关键范围显式传入 |
| 206 | 先改模型再记录失败原因 | 无法复现原始问题 | 检查优化轨迹和源文件版本 | 先保存原始输入、结果和日志 |
| 207 | 把诊断/分析结果写成验收结果 | singularity/workspace 分析被误称 pass | 检查报告类型和 acceptance gate | 分离 analysis 与 acceptance |
| 208 | 没有记录实际样本数 | 空检查或单帧检查被包装成通过 | 检查 report metadata | 统一输出 sample/pair/measurement count |
| 209 | warning、skip、capability_failed 被当作 pass | CI 绿色但核心功能未执行 | 检查退出码和汇总逻辑 | skip/unavailable 必须单独状态 |
| 210 | 只运行 happy path | 命名错、空输入、partial、干涉均未覆盖 | 检查测试矩阵 | 增加负例和边界回归 |
| 211 | 输出路径复用导致结果覆盖 | 读取到旧 motion/package | 检查文件时间、哈希、scenario ID | 每次运行唯一目录 |
| 212 | 验证脚本使用相对路径 | 在 CI/其他 cwd 找到另一模型 | 打印 cwd 和绝对路径 | 解析绝对路径并锁定输入 |

## 13. `.kincheck`、可视化和结果交付错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 213 | 输出路径父目录不存在 | `PACKAGE-OUTPUT-INVALID`、`WRITE-FAILED` | 检查 parent directory | 创建明确输出目录后重试 |
| 214 | 输出文件扩展名错误 | `PACKAGE-EXTENSION-INVALID` | 检查是否为 `.kincheck` | 修扩展名 |
| 215 | assembly 在打包前已无效 | `PACKAGE-ASSEMBLY-INVALID` | 先跑 `validate_assembly()` | 修模型 |
| 216 | MotionResult 与 AssemblyModel 不匹配 | `PACKAGE-ASSEMBLY-MISMATCH`、`MOTION-INVALID` | 比较 IDs 和 metadata | 同一 Scenario 重新求解 |
| 217 | package 缺 manifest | `PACKAGE-MANIFEST-MISSING` | 解压只读检查成员 | 重新打包 |
| 218 | package 缺必需成员 | `PACKAGE-REQUIRED-MEMBER-INVALID` | 检查 assembly/motion/validation JSON | 重新导出 |
| 219 | package member 重复或未被索引 | `PACKAGE-DUPLICATE-MEMBER`、`FILE-UNINDEXED` | 按格式文档校验 ZIP | 使用官方 exporter |
| 220 | package 成员路径不安全 | `PACKAGE-PATH-UNSAFE` | 检查绝对路径、`..`、重复路径 | 拒绝读取 |
| 221 | package hash/size 不匹配 | `PACKAGE-HASH-MISMATCH`、`SIZE-MISMATCH` | 重新计算 SHA256/size | 重新生成包 |
| 222 | package schema 主版本不支持 | `PACKAGE-SCHEMA-UNSUPPORTED` | 检查 manifest schema_version | 使用兼容 Viewer/API |
| 223 | mesh 没有打入包 | `PACKAGE-MESH-MISSING` | 检查 mesh index 和 `missing_mesh_part_ids` | `require_meshes=True` 后重新导出 |
| 224 | mesh scale 缺失或非法 | `PACKAGE-MESH-SCALE-INVALID` | 检查 `scale_to_m` | 修单位并重新打包 |
| 225 | 只在 Viewer 里看起来能动 | Viewer 只回放，不重新求解 | 查看原始 MotionResult 和 validation.json | 以 API 检查报告为准 |
| 226 | Viewer 显示的模型和求解模型不一致 | 网格错位、姿态不匹配 | 比较 assembly JSON 和 mesh mapping | 修 package 资产映射 |
| 227 | package validation 没有在交付前执行 | 损坏包被上传 | 检查发布脚本 | 强制 `validate_package()` |
| 228 | 只交付 `.kincheck`，没有源 map/日志 | 无法解释 source ID 和失败帧 | 检查交付附件 | 同时交付 report、source map、版本信息 |

## 14. 环境、依赖和版本错误

| # | 可能的错误形式 | 常见表象/可能代码 | 如何确认 | 正确处理 |
| ---: | --- | --- | --- | --- |
| 229 | 内置物理后端 未安装或版本不兼容 | backend unavailable/compile failed | 记录 Python、内置物理后端 和 package 版本 | 按锁定依赖安装 |
| 230 | FCL/python-fcl 缺失 | clearance capability failed | 检查 clearance backend | 安装依赖；不能把 skip 当通过 |
| 231 | CADIR exporter 与 KinCheckAPI 版本不匹配 | mapping schema/semantics invalid | 记录两端版本和 commit | 使用兼容版本组合 |
| 232 | CADIR dev 变更了 MJCF 命名或 mapping schema | 旧 converter 突然 name unresolved | 比较 dev commit 和 source map schema | 增加明确版本适配，不猜字段 |
| 233 | 测试使用了旧缓存 | 结果与当前源代码不一致 | 清点缓存路径、文件哈希和时间 | 隔离/刷新缓存 |
| 234 | CI 当前工作目录错误 | 读取同名旧 fixture 或找不到文件 | 记录 cwd 和绝对路径 | 在脚本中解析 repo root |
| 235 | 上游 `simplecadapi` 缺失 | 相关测试 skipped | 查看 skip 原因 | 标记环境缺失，发布前补 CI 依赖 |
| 236 | Python/NumPy/FCL 数值差异 | 边界残差或间隙跨阈值 | 记录平台、版本、容差和重复运行 | 设定合理 tolerance，不能静默放宽 |
| 237 | 并行运行共享输出目录 | 结果相互覆盖或 hash 错误 | 检查进程和输出目录 | 每个运行使用隔离目录 |

## Agent 的最终排查顺序

| 顺序 | 要回答的问题 | 必须留下的证据 |
| ---: | --- | --- |
| 1 | 我使用的 CADIR 产物是否完整且来自同一批次？ | 绝对路径、版本、commit、文件清单、哈希 |
| 2 | XML/mapping/source ID 是否双向一致？ | model ID、对象 ID 集合、source map |
| 3 | 转换后的 AssemblyModel 是否是预期机构？ | component/joint/closure/coupling/ground 数量和 ID |
| 4 | 拓扑、自由度和初始姿态是否合理？ | validation、tree、DOF、初始残差 |
| 5 | Scenario 是否真的表达了用户运动？ | driver、初始状态、duration、sample period、result requests |
| 6 | MotionResult 是否完整？ | status、start/end time、sample count、warnings、last failure |
| 7 | 约束、限位、传动、姿态和轨迹是否满足？ | 每个 CheckReport 的 threshold、evidence、issues、计数 |
| 8 | 干涉/间隙是否在明确范围内执行？ | component pairs、mesh hashes、sampling scope、minimum clearance/events |
| 9 | 是否存在能力缺失而非模型通过？ | backend/FCL capability 状态、skipped 原因 |
| 10 | 交付物是否可复核？ | `.kincheck` validation、motion JSON、source map、运行日志 |

## 结论措辞

Agent 最终只能使用以下三态：

| 结论 | 使用条件 |
| --- | --- |
| **通过** | 所需检查全部执行，结果完整，样本充分，参数合法，所有证据满足阈值 |
| **失败** | 检查实际执行且证据明确不满足，例如闭环残差超限、滑动比错误或出现干涉 |
| **未完成/未验证** | 输入不完整、backend/FCL 不可用、结果为 partial、样本为零或能力不支持 |

“没有发现问题”“脚本退出码为 0”“Viewer 能打开”都不能单独替代上述三态判定。
