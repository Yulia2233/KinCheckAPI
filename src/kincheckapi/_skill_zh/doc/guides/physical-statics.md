# 真实物性与静力（v0.6.0）

本版在 `kincheckapi.dynamics` 中提供物性与静力。旧运动学编译路径保留原契约；禁止把它的占位质量或伺服力当成物理证据。

1. 先冻结 requirements 和独立解析预期，再建模。
2. `measure_package_physics` 校验 CADIR 包并积分每个封闭 BREP；`measure_mass_properties` 接收单个 BREP 与显式 `PhysicsMaterial`。密度不能由名称猜测。
3. `build_dynamics_model` 要求每个实体 occurrence 恰好覆盖一次。重复螺栓不能按定义去重；地面零件仍计入 BOM、质量、静载与编译证据。
4. `compile_dynamics_model` 显式写入质量、质心和惯性参数，并从编译后的主轴/主惯量重构全矩阵；`validate_physics_conversion` 核对逐级转换。
5. `probe_dynamics_capabilities` 按实际操作、拓扑、数据和后端探测。后端可导入不等于能解闭环反力。
6. `StaticRequest` 必须明确重力（包括零重力）、每个标量关节的位置与 free/locked/hold 状态、实际支承及外载。调用 `solve_static_equilibrium` 后还须运行 `check_wrench_balance`、`check_static_load_limits`。
7. `check_static_geometry` 在指定姿态检查全部 BREP 实体配对，包括固定组内部。`ContactRegion` 绑定真实命名面与局部区域；任何实体交叠仍失败。此检查不证明姿态之间连续无碰撞，也不证明摩擦接触稳定。
8. `motion_package(..., dynamics_model=model, static_results=(result, ...))` 增加带哈希索引的 `physics.json`。`read_package` 恢复强类型物性与静力结果；旧包仍可读取，`dynamics_model=None`。viewer 箭头仅示意，数值、参考点、表达帧、来源和状态可查看。

## 单位、惯量和方向

公共量为 m、kg、s、rad、N、N*m、kg*m2。惯量是质心处、在 frame_id 中表达的行优先对称 3×3 全矩阵。Pose 为 xyzw；MuJoCo 为 wxyz。CAD 的 mm 几何产生 mm^5 单位密度惯量积分，乘 kg/m3 密度和 1e-15；质量乘 1e-9。先按 R I Rᵀ 旋转，再按平行轴聚合；纯平移不改变质心惯量。镜像/缩放不能冒充刚性 placement。

载荷作用点和向量均在声明帧表达。力施加到 component_id，施力方为 applied_by；关于 o 的力矩为 R M + (p−o)×R F。保持广义力与公共 B−A 关节坐标共轭。关节 wrench 标明受力子组，父组承受反向 wrench。地面合 wrench 在世界帧、关于世界原点报告。

## 来源与兼容

当前经实测的原生读取器为 SimpleCADAPI 2.1.3b3，使用 canonical ticks。旧 2.0.4b3 包可能使用整数形式的毫米 frame，会被当前读取器明确拒绝。仅通过显式 `sdk_python=...` 选择隔离的旧读取器，记录实际 SDK/编码；没有自动换版本、猜比例或跳过校验。

`read_mjcf_mass_properties` 接受显式 MJCF inertial，并要求另行提供地面物性。仅 density+mesh 返回 `MESH-INERTIA-UNVERIFIED`，不能标成 BREP 真值。已经建成 CAD 实体的 Payload 只声明 cad_occurrence_id，不叠加质量；额外实测质量使用 properties，两者不能同时提供。

`PhysicsManifest` 保存 BREP/材料/版本哈希、原始体积与 mm^5 惯量、位姿、SDK/内核版本及积分预算。JSON 哈希与数值重算共同检出来源、帧和聚合变化。

## 能力边界

首版静力仅覆盖 fixed/revolute/prismatic 树、有效给定位姿和理想固定支承。自由关节存在非零保持需求时失败。多个安装点只返回唯一的合 wrench；强行请求各支点分摊返回 indeterminate。单边或摩擦支承返回 capability_failed。

逆/正动力学、有限驱动力响应、接触力/冲击、应力变形、振动疲劳均未实现。静态额定值超限必须保留为 failed，即使物性转换和力矩平衡通过。示例密度不是材料认证。

通过 `static_checks=(...)` 同时归档额定值等验收报告；超限报告会使物理验收结论保持 false。

## 静力结果包完整性

`kincheck.static/1.1` 保存叠加 payload 前的 `DynamicsModel.base_component_properties`、全部 payload 记录及模型摘要。每个 `StaticResult` 保存 `model_sha256` 和强类型 `request`。写出和读回都按请求重新求解，核对位姿、广义保持力、施加载荷、关节/支承反力、残差及状态；通过结果还必须通过 `check_wrench_balance`。真实且完整的 failed/indeterminate 试验仍可归档，并保留失败状态。仅重算 ZIP 成员哈希不能掩盖物理结果不一致。

摘要用于一致性绑定，不是数字签名。先前没有绑定的开发版 `kincheck.static/1.0` 结果须重新求解并导出；旧运动学包仍可读取。向恢复的模型添加 payload 时，使用其 `base_component_properties` 和已有 `payloads` 加新增记录，避免重复计重并保留来源。

Viewer 用 `sample_count` 保存运动采样数，用 `physics_case_count` 保存静态案例数。静态选择器直接读取各结果的组件位姿，不依赖运动时间或采样数。两条 Viewer 导出路径均提供传动比单位；旧 manifest 缺失单位时显示 `:1`。

静力验收报告必须绑定模型摘要和结果索引。v0.6.0 在写出/读回边界重算额定值和 wrench 平衡报告；未知或未绑定报告不能参与 `acceptance_passed`。

计算验收前会核对序列化的 `static_checks[i].passed` 与重建报告状态。
