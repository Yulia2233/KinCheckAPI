# 运动工况契约

定义路径、位姿、周期和多轴协调目标；不伪造未实现的 6D 求解能力。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`PosePoint`](PosePoint.md) | 类型 | 表示 `PosePoint` 的公开、可序列化数据结构。 |
| [`PoseTrajectory`](PoseTrajectory.md) | 类型 | 表示 `PoseTrajectory` 的公开、可序列化数据结构。 |
| [`PlanarPose`](PlanarPose.md) | 类型 | 表示 `PlanarPose` 的公开、可序列化数据结构。 |
| [`PathTarget`](PathTarget.md) | 类型 | 表示 `PathTarget` 的公开、可序列化数据结构。 |
| [`CoordinatedMotionProfile`](CoordinatedMotionProfile.md) | 类型 | 表示 `CoordinatedMotionProfile` 的公开、可序列化数据结构。 |
| [`PeriodicProfile`](PeriodicProfile.md) | 类型 | 表示 `PeriodicProfile` 的公开、可序列化数据结构。 |
| [`MotionEvent`](MotionEvent.md) | 类型 | 表示 `MotionEvent` 的公开、可序列化数据结构。 |
| [`interpolate_pose`](interpolate_pose.md) | 函数 | 执行公开操作 `interpolate_pose`。 |

## 模块规则

- Targets are immutable records; time values use seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.
