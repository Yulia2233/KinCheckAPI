# 物性、静力与刚体动力学

真实 BREP 物性、树形静力、标量/一般刚体动力学、接触事件和可重放载荷历程。

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
| [`GeneralizedJointState`](GeneralizedJointState.md) | 类型 | 表示 `GeneralizedJointState` 的公开、可序列化数据结构。 |
| [`ConstraintSpec`](ConstraintSpec.md) | 类型 | 表示 `ConstraintSpec` 的公开、可序列化数据结构。 |
| [`ReactionRequest`](ReactionRequest.md) | 类型 | 表示 `ReactionRequest` 的公开、可序列化数据结构。 |
| [`RigidDynamicsScenario`](RigidDynamicsScenario.md) | 类型 | 表示 `RigidDynamicsScenario` 的公开、可序列化数据结构。 |
| [`MultibodySample`](MultibodySample.md) | 类型 | 表示 `MultibodySample` 的公开、可序列化数据结构。 |
| [`MultibodyResult`](MultibodyResult.md) | 类型 | 表示 `MultibodyResult` 的公开、可序列化数据结构。 |
| [`probe_multibody_capabilities`](probe_multibody_capabilities.md) | 函数 | 执行公开操作 `probe_multibody_capabilities`。 |
| [`solve_multibody_dynamics`](solve_multibody_dynamics.md) | 函数 | 求解指定运动学问题：`solve_multibody_dynamics`。 |
| [`DynamicsScenarioCase`](DynamicsScenarioCase.md) | 类型 | 表示 `DynamicsScenarioCase` 的公开、可序列化数据结构。 |
| [`DynamicsScenarioMatrix`](DynamicsScenarioMatrix.md) | 类型 | 表示 `DynamicsScenarioMatrix` 的公开、可序列化数据结构。 |
| [`DynamicsScenarioSuite`](DynamicsScenarioSuite.md) | 类型 | 表示 `DynamicsScenarioSuite` 的公开、可序列化数据结构。 |
| [`run_dynamics_cases`](run_dynamics_cases.md) | 函数 | 执行公开操作 `run_dynamics_cases`。 |
| [`ContactInterface`](ContactInterface.md) | 类型 | 表示 `ContactInterface` 的公开、可序列化数据结构。 |
| [`ContactEvent`](ContactEvent.md) | 类型 | 表示 `ContactEvent` 的公开、可序列化数据结构。 |
| [`ContactDynamicsResult`](ContactDynamicsResult.md) | 类型 | 表示 `ContactDynamicsResult` 的公开、可序列化数据结构。 |
| [`solve_contact_dynamics`](solve_contact_dynamics.md) | 函数 | 求解指定运动学问题：`solve_contact_dynamics`。 |
| [`check_contact_convergence`](check_contact_convergence.md) | 函数 | 执行结构化检查：`check_contact_convergence`。 |
| [`ControllerSpec`](ControllerSpec.md) | 类型 | 表示 `ControllerSpec` 的公开、可序列化数据结构。 |
| [`ActuatorEnvelope`](ActuatorEnvelope.md) | 类型 | 表示 `ActuatorEnvelope` 的公开、可序列化数据结构。 |
| [`JointFriction`](JointFriction.md) | 类型 | 表示 `JointFriction` 的公开、可序列化数据结构。 |
| [`BrakePolicy`](BrakePolicy.md) | 类型 | 表示 `BrakePolicy` 的公开、可序列化数据结构。 |
| [`check_actuator_limits`](check_actuator_limits.md) | 函数 | 执行结构化检查：`check_actuator_limits`。 |
| [`WrenchSample`](WrenchSample.md) | 类型 | 表示 `WrenchSample` 的公开、可序列化数据结构。 |
| [`WrenchProfile`](WrenchProfile.md) | 类型 | 表示 `WrenchProfile` 的公开、可序列化数据结构。 |
| [`RandomExcitation`](RandomExcitation.md) | 类型 | 表示 `RandomExcitation` 的公开、可序列化数据结构。 |
| [`DutyCycle`](DutyCycle.md) | 类型 | 表示 `DutyCycle` 的公开、可序列化数据结构。 |
| [`DynamicsLoadHistory`](DynamicsLoadHistory.md) | 类型 | 表示 `DynamicsLoadHistory` 的公开、可序列化数据结构。 |
| [`history_from_multibody_result`](history_from_multibody_result.md) | 函数 | 执行公开操作 `history_from_multibody_result`。 |
| [`record_dynamics_history`](record_dynamics_history.md) | 函数 | 执行公开操作 `record_dynamics_history`。 |
| [`summarize_drive_duty`](summarize_drive_duty.md) | 函数 | 执行公开操作 `summarize_drive_duty`。 |
| [`summarize_energy`](summarize_energy.md) | 函数 | 执行公开操作 `summarize_energy`。 |
| [`export_load_history`](export_load_history.md) | 函数 | 导出公开结果资产：`export_load_history`。 |
| [`read_load_history`](read_load_history.md) | 函数 | 读取并重建公开对象：`read_load_history`。 |

## 模块规则

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触容量 API 只检查给定外力；v0.7 刚体接触/冲量 API 必须保留接触状态、动量、能量和收敛证据。
- 结构网格、应力、结构振动和疲劳属于独立 FEACheckAPI；KinCheckAPI 只导出运动、刚体载荷、反力和冲量事实。
