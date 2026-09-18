# 验收检查

把用户命题转换成结构化、可复核的运动学检查。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`CheckReport`](CheckReport.md) | 类型 | 表示 `CheckReport` 的公开、可序列化数据结构。 |
| [`CheckSpec`](CheckSpec.md) | 类型 | 表示 `CheckSpec` 的公开、可序列化数据结构。 |
| [`CheckSuiteReport`](CheckSuiteReport.md) | 类型 | 表示 `CheckSuiteReport` 的公开、可序列化数据结构。 |
| [`DriverTrackingReport`](DriverTrackingReport.md) | 类型 | 表示 `DriverTrackingReport` 的公开、可序列化数据结构。 |
| [`CheckType`](CheckType.md) | 类型别名 | 定义 `CheckType` 使用的公开类型约定。 |
| [`Direction`](Direction.md) | 类型别名 | 定义 `Direction` 使用的公开类型约定。 |
| [`RatioMeasurement`](RatioMeasurement.md) | 类型别名 | 定义 `RatioMeasurement` 使用的公开类型约定。 |
| [`AssemblyIntegrityReport`](AssemblyIntegrityReport.md) | 类型 | 表示 `AssemblyIntegrityReport` 的公开、可序列化数据结构。 |
| [`ContainmentRelation`](ContainmentRelation.md) | 类型 | 表示 `ContainmentRelation` 的公开、可序列化数据结构。 |
| [`IntegrityRelationResult`](IntegrityRelationResult.md) | 类型 | 表示 `IntegrityRelationResult` 的公开、可序列化数据结构。 |
| [`check_assembly_integrity`](check_assembly_integrity.md) | 函数 | 在静态或 MotionResult 的每个采样状态检查 Component 是否仍属于一个完整连接网络，并报告断开、脱离和越界。 |
| [`check_constraint_equation_residuals`](check_constraint_equation_residuals.md) | 函数 | 执行结构化检查：`check_constraint_equation_residuals`。 |
| [`check_constraint_residuals`](check_constraint_residuals.md) | 函数 | 执行结构化检查：`check_constraint_residuals`。 |
| [`check_driver_tracking`](check_driver_tracking.md) | 函数 | 执行结构化检查：`check_driver_tracking`。 |
| [`check_joint_limits`](check_joint_limits.md) | 函数 | 执行结构化检查：`check_joint_limits`。 |
| [`check_interference`](check_interference.md) | 函数 | 检查离散运动样本中的指定组件对是否发生网格穿透。 |
| [`check_minimum_clearance`](check_minimum_clearance.md) | 函数 | 执行结构化检查：`check_minimum_clearance`。 |
| [`check_motion_envelope`](check_motion_envelope.md) | 函数 | 执行结构化检查：`check_motion_envelope`。 |
| [`check_pose_target`](check_pose_target.md) | 函数 | 执行结构化检查：`check_pose_target`。 |
| [`check_pose_trajectory`](check_pose_trajectory.md) | 函数 | 执行结构化检查：`check_pose_trajectory`。 |
| [`check_path_tracking`](check_path_tracking.md) | 函数 | 执行结构化检查：`check_path_tracking`。 |
| [`check_planar_tracking`](check_planar_tracking.md) | 函数 | 执行结构化检查：`check_planar_tracking`。 |
| [`check_start_stop_reversal`](check_start_stop_reversal.md) | 函数 | 执行结构化检查：`check_start_stop_reversal`。 |
| [`check_periodic_motion`](check_periodic_motion.md) | 函数 | 执行结构化检查：`check_periodic_motion`。 |
| [`check_synchronization`](check_synchronization.md) | 函数 | 执行结构化检查：`check_synchronization`。 |
| [`check_continuous_interference`](check_continuous_interference.md) | 函数 | 执行结构化检查：`check_continuous_interference`。 |
| [`check_trajectory`](check_trajectory.md) | 函数 | 执行结构化检查：`check_trajectory`。 |
| [`check_transmission_ratio`](check_transmission_ratio.md) | 函数 | 执行结构化检查：`check_transmission_ratio`。 |
| [`run_checks`](run_checks.md) | 函数 | 按 `CheckSpec` 顺序执行显式验收命题，返回 `CheckSuiteReport`。 |

## 模块规则

- 检查必须对应明确的对象、时间窗、期望值、阈值和单位。
- 检查对象为空、证据为空或 MotionResult 不完整时不得通过。
- `CheckReport.passed` 是最终布尔结论；同时保留 evidence、issues 和 metadata。
- 装配体整体性检查支持任意数量的 Component；`component_ids=None` 检查整个装配体。
- 机械、容纳/导向和几何连接共同形成连接图；几何连接必须记录米制容差。
