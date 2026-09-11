# 结果模型与查询

读取 MotionResult 中的状态、轨迹、残差和事件证据。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`ComponentState`](ComponentState.md) | 类型 | 表示 `ComponentState` 的公开、可序列化数据结构。 |
| [`ConnectorState`](ConnectorState.md) | 类型 | 表示 `ConnectorState` 的公开、可序列化数据结构。 |
| [`ConstraintResidual`](ConstraintResidual.md) | 类型 | 表示 `ConstraintResidual` 的公开、可序列化数据结构。 |
| [`ConstraintEquationResidual`](ConstraintEquationResidual.md) | 类型 | 表示 `ConstraintEquationResidual` 的公开、可序列化数据结构。 |
| [`ConstraintEquationType`](ConstraintEquationType.md) | 类型别名 | 定义 `ConstraintEquationType` 使用的公开类型约定。 |
| [`ConstraintEquationUnit`](ConstraintEquationUnit.md) | 类型别名 | 定义 `ConstraintEquationUnit` 使用的公开类型约定。 |
| [`Direction`](Direction.md) | 类型别名 | 定义 `Direction` 使用的公开类型约定。 |
| [`InterferenceEvent`](InterferenceEvent.md) | 类型 | 表示 `InterferenceEvent` 的公开、可序列化数据结构。 |
| [`InterferenceResult`](InterferenceResult.md) | 类型 | 表示 `InterferenceResult` 的公开、可序列化数据结构。 |
| [`JointExtrema`](JointExtrema.md) | 类型 | 表示 `JointExtrema` 的公开、可序列化数据结构。 |
| [`JointState`](JointState.md) | 类型 | 表示 `JointState` 的公开、可序列化数据结构。 |
| [`JointTrajectory`](JointTrajectory.md) | 类型 | 表示 `JointTrajectory` 的公开、可序列化数据结构。 |
| [`LimitEvent`](LimitEvent.md) | 类型 | 表示 `LimitEvent` 的公开、可序列化数据结构。 |
| [`MotionResult`](MotionResult.md) | 类型 | 表示 `MotionResult` 的公开、可序列化数据结构。 |
| [`MotionStatus`](MotionStatus.md) | 类型别名 | 定义 `MotionStatus` 使用的公开类型约定。 |
| [`MotionSummary`](MotionSummary.md) | 类型 | 表示 `MotionSummary` 的公开、可序列化数据结构。 |
| [`Trajectory`](Trajectory.md) | 类型 | 表示 `Trajectory` 的公开、可序列化数据结构。 |
| [`TransmissionRatioCheck`](TransmissionRatioCheck.md) | 类型 | 表示 `TransmissionRatioCheck` 的公开、可序列化数据结构。 |
| [`list_constraint_residuals`](list_constraint_residuals.md) | 函数 | 筛选并返回已记录的结构化证据：`list_constraint_residuals`。 |
| [`list_constraint_equation_residuals`](list_constraint_equation_residuals.md) | 函数 | 筛选并返回已记录的结构化证据：`list_constraint_equation_residuals`。 |
| [`list_interference_events`](list_interference_events.md) | 函数 | 筛选并返回已记录的结构化证据：`list_interference_events`。 |
| [`list_limit_events`](list_limit_events.md) | 函数 | 筛选并返回已记录的结构化证据：`list_limit_events`。 |
| [`read_component_pose`](read_component_pose.md) | 函数 | 在指定时间读取或插值一个组件的世界姿态。 |
| [`read_component_state`](read_component_state.md) | 函数 | 读取组件世界姿态以及结果中可用的线/角速度和加速度。 |
| [`read_connector_state`](read_connector_state.md) | 函数 | 读取指定 connector 的世界姿态和可用空间运动状态。 |
| [`read_joint_state`](read_joint_state.md) | 函数 | 在指定时间读取或插值一个 joint 的位置、速度和加速度状态。 |
| [`read_trajectory`](read_trajectory.md) | 函数 | 返回结果中已经记录的组件或 connector 完整轨迹。 |
| [`summarize_motion`](summarize_motion.md) | 函数 | 汇总状态、时长、样本数、joint extrema、最大残差和事件计数。 |
| [`write_motion_result`](write_motion_result.md) | 函数 | 将完整公开运动结果写为确定性的 JSON。 |

## 模块规则

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。
