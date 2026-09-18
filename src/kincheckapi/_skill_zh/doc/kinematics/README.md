# 运动学求解与分析

执行位置和连续运动求解，并分析自由度、Jacobian、奇异性和工作空间。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`KinematicSolveOptions`](KinematicSolveOptions.md) | 类型 | 表示 `KinematicSolveOptions` 的公开、可序列化数据结构。 |
| [`KinematicCapabilities`](KinematicCapabilities.md) | 类型 | 表示 `KinematicCapabilities` 的公开、可序列化数据结构。 |
| [`ClosureReport`](ClosureReport.md) | 类型 | 表示 `ClosureReport` 的公开、可序列化数据结构。 |
| [`ConnectorPathResult`](ConnectorPathResult.md) | 类型 | 表示 `ConnectorPathResult` 的公开、可序列化数据结构。 |
| [`DofReport`](DofReport.md) | 类型 | 表示 `DofReport` 的公开、可序列化数据结构。 |
| [`JacobianOptions`](JacobianOptions.md) | 类型 | 表示 `JacobianOptions` 的公开、可序列化数据结构。 |
| [`JacobianResult`](JacobianResult.md) | 类型 | 表示 `JacobianResult` 的公开、可序列化数据结构。 |
| [`MobilityReport`](MobilityReport.md) | 类型 | 表示 `MobilityReport` 的公开、可序列化数据结构。 |
| [`PoseTarget`](PoseTarget.md) | 类型 | 表示 `PoseTarget` 的公开、可序列化数据结构。 |
| [`PositionSolveOptions`](PositionSolveOptions.md) | 类型 | 表示 `PositionSolveOptions` 的公开、可序列化数据结构。 |
| [`ReachabilityOptions`](ReachabilityOptions.md) | 类型 | 表示 `ReachabilityOptions` 的公开、可序列化数据结构。 |
| [`PositionResult`](PositionResult.md) | 类型 | 表示 `PositionResult` 的公开、可序列化数据结构。 |
| [`ReachabilityResult`](ReachabilityResult.md) | 类型 | 表示 `ReachabilityResult` 的公开、可序列化数据结构。 |
| [`SingularityReport`](SingularityReport.md) | 类型 | 表示 `SingularityReport` 的公开、可序列化数据结构。 |
| [`SingularityOptions`](SingularityOptions.md) | 类型 | 表示 `SingularityOptions` 的公开、可序列化数据结构。 |
| [`SingularitySample`](SingularitySample.md) | 类型 | 表示 `SingularitySample` 的公开、可序列化数据结构。 |
| [`SolveAttempt`](SolveAttempt.md) | 类型 | 表示 `SolveAttempt` 的公开、可序列化数据结构。 |
| [`TargetReference`](TargetReference.md) | 类型 | 表示 `TargetReference` 的公开、可序列化数据结构。 |
| [`WorkspaceOptions`](WorkspaceOptions.md) | 类型 | 表示 `WorkspaceOptions` 的公开、可序列化数据结构。 |
| [`WorkspaceResult`](WorkspaceResult.md) | 类型 | 表示 `WorkspaceResult` 的公开、可序列化数据结构。 |
| [`WorkspaceSample`](WorkspaceSample.md) | 类型 | 表示 `WorkspaceSample` 的公开、可序列化数据结构。 |
| [`analyze_dofs`](analyze_dofs.md) | 函数 | 分析机构或结果的运动学性质：`analyze_dofs`。 |
| [`backend_capabilities`](backend_capabilities.md) | 函数 | 执行公开操作 `backend_capabilities`。 |
| [`analyze_mobility`](analyze_mobility.md) | 函数 | 根据名义关节自由度和约束 Jacobian 秩分析机构的有效自由度。 |
| [`check_reachability`](check_reachability.md) | 函数 | 执行结构化检查：`check_reachability`。 |
| [`compute_workspace`](compute_workspace.md) | 函数 | 计算后端无关的运动学量：`compute_workspace`。 |
| [`compute_jacobian`](compute_jacobian.md) | 函数 | 对指定组件或 connector 在给定 joint positions 下计算后端无关的六维有限差分 Jacobian。 |
| [`find_singularities`](find_singularities.md) | 函数 | 在 MotionResult 的实际采样上计算 Jacobian 秩、最小奇异值和条件数，报告 singular/near-singular 样本。 |
| [`solve_motion`](solve_motion.md) | 函数 | 沿 Scenario 时间窗执行连续运动学求解，返回后端无关的 `MotionResult`。 |
| [`solve_position`](solve_position.md) | 函数 | 求解指定运动学问题：`solve_position`。 |
| [`trace_connector_path`](trace_connector_path.md) | 函数 | 从已记录 connector 轨迹计算时间序列、路径长度、起终点和世界坐标 bounds。 |
| [`try_solve_motion`](try_solve_motion.md) | 函数 | 在失败时保留结构化报告和 `last_valid_result`；不会把失败转换成通过。 |
| [`validate_closures`](validate_closures.md) | 函数 | 聚合验证输入契约：`validate_closures`。 |
| [`verify_transmission_ratio`](verify_transmission_ratio.md) | 函数 | 弃用的兼容入口；新代码使用 `kincheckapi.checks.check_transmission_ratio()`。 |
| [`write_motion_result`](write_motion_result.md) | 函数 | 将完整公开运动结果写为确定性的 JSON。 |
| [`solve_inverse_kinematics`](solve_inverse_kinematics.md) | 函数 | 求解指定运动学问题：`solve_inverse_kinematics`。 |

## 模块规则

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。
