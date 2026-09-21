# 动力学命名空间

真实 BREP 物性、树形静力、标量树逆/正动力学，以及给定外力的接触摩擦容量检查。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`ContactRegion`](ContactRegion.md) | 类型 | 表示 `ContactRegion` 的公开、可序列化数据结构。 |
| [`check_static_geometry`](check_static_geometry.md) | 函数 | 执行结构化检查：`check_static_geometry`。 |
| [`check_occurrence_support`](check_occurrence_support.md) | 函数 | 执行结构化检查：`check_occurrence_support`。 |
| [`DynamicState`](DynamicState.md) | 类型 | 表示 `DynamicState` 的公开、可序列化数据结构。 |
| [`DynamicRequest`](DynamicRequest.md) | 类型 | 表示 `DynamicRequest` 的公开、可序列化数据结构。 |
| [`InverseDynamicsResult`](InverseDynamicsResult.md) | 类型 | 表示 `InverseDynamicsResult` 的公开、可序列化数据结构。 |
| [`ActuatorSpec`](ActuatorSpec.md) | 类型 | 表示 `ActuatorSpec` 的公开、可序列化数据结构。 |
| [`ActuatorProfile`](ActuatorProfile.md) | 类型 | 表示 `ActuatorProfile` 的公开、可序列化数据结构。 |
| [`ForwardDynamicsRequest`](ForwardDynamicsRequest.md) | 类型 | 表示 `ForwardDynamicsRequest` 的公开、可序列化数据结构。 |
| [`DynamicSample`](DynamicSample.md) | 类型 | 表示 `DynamicSample` 的公开、可序列化数据结构。 |
| [`ForwardDynamicsResult`](ForwardDynamicsResult.md) | 类型 | 表示 `ForwardDynamicsResult` 的公开、可序列化数据结构。 |
| [`ContactSpec`](ContactSpec.md) | 类型 | 表示 `ContactSpec` 的公开、可序列化数据结构。 |
| [`ContactReport`](ContactReport.md) | 类型 | 表示 `ContactReport` 的公开、可序列化数据结构。 |
| [`solve_inverse_dynamics`](solve_inverse_dynamics.md) | 函数 | 求解指定运动学问题：`solve_inverse_dynamics`。 |
| [`solve_forward_dynamics`](solve_forward_dynamics.md) | 函数 | 求解指定运动学问题：`solve_forward_dynamics`。 |
| [`check_dynamic_load_limits`](check_dynamic_load_limits.md) | 函数 | 执行结构化检查：`check_dynamic_load_limits`。 |
| [`check_dynamic_tracking`](check_dynamic_tracking.md) | 函数 | 执行结构化检查：`check_dynamic_tracking`。 |
| [`check_contact_capacity`](check_contact_capacity.md) | 函数 | 执行结构化检查：`check_contact_capacity`。 |
| [`read_mjcf_mass_properties`](read_mjcf_mass_properties.md) | 函数 | 读取并重建公开对象：`read_mjcf_mass_properties`。 |
| [`measure_interface_centers`](measure_interface_centers.md) | 函数 | 执行公开操作 `measure_interface_centers`。 |
| [`DynamicsModel`](DynamicsModel.md) | 类型 | 表示 `DynamicsModel` 的公开、可序列化数据结构。 |
| [`GravityField`](GravityField.md) | 类型 | 表示 `GravityField` 的公开、可序列化数据结构。 |
| [`Payload`](Payload.md) | 类型 | 表示 `Payload` 的公开、可序列化数据结构。 |
| [`PhysicsError`](PhysicsError.md) | 类型 | 表示 `PhysicsError` 的公开、可序列化数据结构。 |
| [`PhysicsManifest`](PhysicsManifest.md) | 类型 | 表示 `PhysicsManifest` 的公开、可序列化数据结构。 |
| [`PhysicsMaterial`](PhysicsMaterial.md) | 类型 | 表示 `PhysicsMaterial` 的公开、可序列化数据结构。 |
| [`PhysicsOccurrence`](PhysicsOccurrence.md) | 类型 | 表示 `PhysicsOccurrence` 的公开、可序列化数据结构。 |
| [`PhysicsReport`](PhysicsReport.md) | 类型 | 表示 `PhysicsReport` 的公开、可序列化数据结构。 |
| [`RigidBodyProperties`](RigidBodyProperties.md) | 类型 | 表示 `RigidBodyProperties` 的公开、可序列化数据结构。 |
| [`StaticRequest`](StaticRequest.md) | 类型 | 表示 `StaticRequest` 的公开、可序列化数据结构。 |
| [`StaticResult`](StaticResult.md) | 类型 | 表示 `StaticResult` 的公开、可序列化数据结构。 |
| [`SupportSpec`](SupportSpec.md) | 类型 | 表示 `SupportSpec` 的公开、可序列化数据结构。 |
| [`WrenchLoad`](WrenchLoad.md) | 类型 | 表示 `WrenchLoad` 的公开、可序列化数据结构。 |
| [`aggregate_mass_properties`](aggregate_mass_properties.md) | 函数 | 执行公开操作 `aggregate_mass_properties`。 |
| [`build_dynamics_model`](build_dynamics_model.md) | 函数 | 执行公开操作 `build_dynamics_model`。 |
| [`check_mass_properties`](check_mass_properties.md) | 函数 | 执行结构化检查：`check_mass_properties`。 |
| [`measure_mass_properties`](measure_mass_properties.md) | 函数 | 执行公开操作 `measure_mass_properties`。 |
| [`transform_mass_properties`](transform_mass_properties.md) | 函数 | 执行公开操作 `transform_mass_properties`。 |
| [`measure_package_physics`](measure_package_physics.md) | 函数 | 执行公开操作 `measure_package_physics`。 |
| [`DynamicsCompilation`](DynamicsCompilation.md) | 类型 | 表示 `DynamicsCompilation` 的公开、可序列化数据结构。 |
| [`compile_dynamics_model`](compile_dynamics_model.md) | 函数 | 执行公开操作 `compile_dynamics_model`。 |
| [`validate_physics_conversion`](validate_physics_conversion.md) | 函数 | 聚合验证输入契约：`validate_physics_conversion`。 |
| [`check_static_load_limits`](check_static_load_limits.md) | 函数 | 执行结构化检查：`check_static_load_limits`。 |
| [`check_support`](check_support.md) | 函数 | 执行结构化检查：`check_support`。 |
| [`check_wrench_balance`](check_wrench_balance.md) | 函数 | 执行结构化检查：`check_wrench_balance`。 |
| [`probe_dynamics_capabilities`](probe_dynamics_capabilities.md) | 函数 | 执行公开操作 `probe_dynamics_capabilities`。 |
| [`solve_static_equilibrium`](solve_static_equilibrium.md) | 函数 | 求解指定运动学问题：`solve_static_equilibrium`。 |

## 模块规则

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应、碰撞冲量、结构、振动或疲劳结论。
