# Scenario 与驱动

定义初态、驱动、运行时间、采样和结果记录范围。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`ComponentResultScope`](ComponentResultScope.md) | 枚举 | 定义 `ComponentResultScope` 接受的稳定枚举值。 |
| [`ComponentResultRequest`](ComponentResultRequest.md) | 类型 | 表示 `ComponentResultRequest` 的公开、可序列化数据结构。 |
| [`Interpolation`](Interpolation.md) | 枚举 | 定义 `Interpolation` 接受的稳定枚举值。 |
| [`JointLock`](JointLock.md) | 类型 | 表示 `JointLock` 的公开、可序列化数据结构。 |
| [`JointResultRequest`](JointResultRequest.md) | 类型 | 表示 `JointResultRequest` 的公开、可序列化数据结构。 |
| [`JointValue`](JointValue.md) | 类型 | 表示 `JointValue` 的公开、可序列化数据结构。 |
| [`MotionProfile`](MotionProfile.md) | 类型 | 表示 `MotionProfile` 的公开、可序列化数据结构。 |
| [`PositionDriver`](PositionDriver.md) | 类型 | 表示 `PositionDriver` 的公开、可序列化数据结构。 |
| [`Profile`](Profile.md) | 类型别名 | 定义 `Profile` 使用的公开类型约定。 |
| [`ProfilePoint`](ProfilePoint.md) | 类型 | 表示 `ProfilePoint` 的公开、可序列化数据结构。 |
| [`Scenario`](Scenario.md) | 类型 | 表示 `Scenario` 的公开、可序列化数据结构。 |
| [`SpeedDriver`](SpeedDriver.md) | 类型 | 表示 `SpeedDriver` 的公开、可序列化数据结构。 |
| [`add_joint_position_driver`](add_joint_position_driver.md) | 函数 | 添加并返回更新后的不可变对象：`add_joint_position_driver`。 |
| [`add_joint_speed_driver`](add_joint_speed_driver.md) | 函数 | 添加并返回更新后的不可变对象：`add_joint_speed_driver`。 |
| [`add_joint_speed_profile`](add_joint_speed_profile.md) | 函数 | 添加并返回更新后的不可变对象：`add_joint_speed_profile`。 |
| [`create_scenario`](create_scenario.md) | 函数 | 创建公开对象：`create_scenario`。 |
| [`disable_constraint`](disable_constraint.md) | 函数 | 在 Scenario 中按稳定 ID 禁用约束；只用于明确的诊断或对照工况。 |
| [`lock_joint`](lock_joint.md) | 函数 | 在 Scenario 中锁定指定 joint，可选给出锁定位置；这会改变待验证工况。 |
| [`read_scenario`](read_scenario.md) | 函数 | 读取并重建公开对象：`read_scenario`。 |
| [`request_component_result`](request_component_result.md) | 函数 | 请求在结果中记录指定对象：`request_component_result`。 |
| [`request_joint_result`](request_joint_result.md) | 函数 | 请求在结果中记录指定对象：`request_joint_result`。 |
| [`scenario_from_dict`](scenario_from_dict.md) | 函数 | 从已经解析的 mapping 重建与指定 AssemblyModel 绑定的 Scenario；严格校验需另行执行。 |
| [`scenario_to_dict`](scenario_to_dict.md) | 函数 | 把 Scenario 转换为 JSON 兼容的确定性字典。 |
| [`set_initial_joint_position`](set_initial_joint_position.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_initial_joint_position`。 |
| [`set_initial_joint_velocity`](set_initial_joint_velocity.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_initial_joint_velocity`。 |
| [`set_component_result_scope`](set_component_result_scope.md) | 函数 | 选择组件轨迹记录范围。`all` 始终记录全部组件；`requested` 在请求列表非空时仅记录所请求对象，在空列表时保留历史兼容行为并记录全部组件。 |
| [`set_capture_integration_steps`](set_capture_integration_steps.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_capture_integration_steps`。 |
| [`set_joint_home_position`](set_joint_home_position.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_joint_home_position`。 |
| [`set_run_duration`](set_run_duration.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_run_duration`。 |
| [`set_sample_period`](set_sample_period.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_sample_period`。 |
| [`validate_scenario`](validate_scenario.md) | 函数 | 聚合验证输入契约：`validate_scenario`。 |
| [`write_scenario`](write_scenario.md) | 函数 | 把公开对象确定性写出：`write_scenario`。 |

## 模块规则

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。
