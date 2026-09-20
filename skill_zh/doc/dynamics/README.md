# 动力学命名空间

真实 BREP 物性、载荷与支承、树形标量关节静平衡及后端惯量核验。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`ContactRegion`](ContactRegion.md) | 类型 | 表示 `ContactRegion` 的公开、可序列化数据结构。 |
| [`check_static_geometry`](check_static_geometry.md) | 函数 | 执行结构化检查：`check_static_geometry`。 |
| [`check_occurrence_support`](check_occurrence_support.md) | 函数 | 执行结构化检查：`check_occurrence_support`。 |
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
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。
