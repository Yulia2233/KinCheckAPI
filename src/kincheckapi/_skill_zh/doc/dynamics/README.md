# 动力学、结构、振动与疲劳

真实 BREP 物性、树形动力学，以及显式结构模型上的强度、振动和疲劳参考检查。

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
| [`ElasticMaterial`](ElasticMaterial.md) | 类型 | 表示 `ElasticMaterial` 的公开、可序列化数据结构。 |
| [`FailureCriterion`](FailureCriterion.md) | 类型 | 表示 `FailureCriterion` 的公开、可序列化数据结构。 |
| [`StructuralLoad`](StructuralLoad.md) | 类型 | 表示 `StructuralLoad` 的公开、可序列化数据结构。 |
| [`StructuralModel`](StructuralModel.md) | 类型 | 表示 `StructuralModel` 的公开、可序列化数据结构。 |
| [`LoadTransferMap`](LoadTransferMap.md) | 类型 | 表示 `LoadTransferMap` 的公开、可序列化数据结构。 |
| [`StructuralResult`](StructuralResult.md) | 类型 | 表示 `StructuralResult` 的公开、可序列化数据结构。 |
| [`BucklingResult`](BucklingResult.md) | 类型 | 表示 `BucklingResult` 的公开、可序列化数据结构。 |
| [`transfer_loads`](transfer_loads.md) | 函数 | 执行公开操作 `transfer_loads`。 |
| [`solve_static_structure`](solve_static_structure.md) | 函数 | 求解指定运动学问题：`solve_static_structure`。 |
| [`solve_buckling_screening`](solve_buckling_screening.md) | 函数 | 求解指定运动学问题：`solve_buckling_screening`。 |
| [`check_stress`](check_stress.md) | 函数 | 执行结构化检查：`check_stress`。 |
| [`check_deflection`](check_deflection.md) | 函数 | 执行结构化检查：`check_deflection`。 |
| [`check_structural_margin`](check_structural_margin.md) | 函数 | 执行结构化检查：`check_structural_margin`。 |
| [`ModalRequest`](ModalRequest.md) | 类型 | 表示 `ModalRequest` 的公开、可序列化数据结构。 |
| [`DampingSpec`](DampingSpec.md) | 类型 | 表示 `DampingSpec` 的公开、可序列化数据结构。 |
| [`ModalResult`](ModalResult.md) | 类型 | 表示 `ModalResult` 的公开、可序列化数据结构。 |
| [`FrequencyResponseResult`](FrequencyResponseResult.md) | 类型 | 表示 `FrequencyResponseResult` 的公开、可序列化数据结构。 |
| [`TransientResult`](TransientResult.md) | 类型 | 表示 `TransientResult` 的公开、可序列化数据结构。 |
| [`RandomLoadSpec`](RandomLoadSpec.md) | 类型 | 表示 `RandomLoadSpec` 的公开、可序列化数据结构。 |
| [`PSDResult`](PSDResult.md) | 类型 | 表示 `PSDResult` 的公开、可序列化数据结构。 |
| [`solve_modes`](solve_modes.md) | 函数 | 求解指定运动学问题：`solve_modes`。 |
| [`solve_frequency_response`](solve_frequency_response.md) | 函数 | 求解指定运动学问题：`solve_frequency_response`。 |
| [`solve_transient_response`](solve_transient_response.md) | 函数 | 求解指定运动学问题：`solve_transient_response`。 |
| [`estimate_psd`](estimate_psd.md) | 函数 | 执行公开操作 `estimate_psd`。 |
| [`compute_rms`](compute_rms.md) | 函数 | 计算后端无关的运动学量：`compute_rms`。 |
| [`check_resonance_margin`](check_resonance_margin.md) | 函数 | 执行结构化检查：`check_resonance_margin`。 |
| [`check_vibration_limits`](check_vibration_limits.md) | 函数 | 执行结构化检查：`check_vibration_limits`。 |
| [`StressHistory`](StressHistory.md) | 类型 | 表示 `StressHistory` 的公开、可序列化数据结构。 |
| [`FatigueMaterial`](FatigueMaterial.md) | 类型 | 表示 `FatigueMaterial` 的公开、可序列化数据结构。 |
| [`MeanStressCorrection`](MeanStressCorrection.md) | 类型 | 表示 `MeanStressCorrection` 的公开、可序列化数据结构。 |
| [`FatigueCycle`](FatigueCycle.md) | 类型 | 表示 `FatigueCycle` 的公开、可序列化数据结构。 |
| [`FatigueReport`](FatigueReport.md) | 类型 | 表示 `FatigueReport` 的公开、可序列化数据结构。 |
| [`DutyCycle`](DutyCycle.md) | 类型 | 表示 `DutyCycle` 的公开、可序列化数据结构。 |
| [`ScenarioMatrix`](ScenarioMatrix.md) | 类型 | 表示 `ScenarioMatrix` 的公开、可序列化数据结构。 |
| [`OperatingEnvelopeReport`](OperatingEnvelopeReport.md) | 类型 | 表示 `OperatingEnvelopeReport` 的公开、可序列化数据结构。 |
| [`DriveDutySummary`](DriveDutySummary.md) | 类型 | 表示 `DriveDutySummary` 的公开、可序列化数据结构。 |
| [`count_cycles`](count_cycles.md) | 函数 | 执行公开操作 `count_cycles`。 |
| [`evaluate_fatigue`](evaluate_fatigue.md) | 函数 | 执行公开操作 `evaluate_fatigue`。 |
| [`evaluate_operating_envelope`](evaluate_operating_envelope.md) | 函数 | 执行公开操作 `evaluate_operating_envelope`。 |
| [`summarize_drive_duty`](summarize_drive_duty.md) | 函数 | 执行公开操作 `summarize_drive_duty`。 |
| [`summarize_energy`](summarize_energy.md) | 函数 | 执行公开操作 `summarize_energy`。 |
| [`check_fatigue_limits`](check_fatigue_limits.md) | 函数 | 执行结构化检查：`check_fatigue_limits`。 |

## 模块规则

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应或碰撞冲量。
- 结构、振动和疲劳 API 只对显式线性矩阵、声明材料、应力历程和 S-N 曲线给出可追溯参考结果；自动 BREP 网格、非线性接触、塑性/断裂及非线性振动返回能力边界。
