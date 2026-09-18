# Motion Contract Targets

Define path, pose, periodic, and coordinated targets without claiming unsupported 6D solving.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`PosePoint`](PosePoint.md) | Type | PosePoint(*, time_s: 'float', pose: 'Pose') |
| [`PoseTrajectory`](PoseTrajectory.md) | Type | A world-frame, time-indexed acceptance target, not a Cartesian driver. |
| [`PlanarPose`](PlanarPose.md) | Type | PlanarPose(*, time_s: 'float', x_m: 'float', y_m: 'float', yaw_rad: 'float') |
| [`PathTarget`](PathTarget.md) | Type | Geometric polyline target. This does not prescribe timing or traversal. |
| [`CoordinatedMotionProfile`](CoordinatedMotionProfile.md) | Type | Scalar joint position targets sharing one time axis. |
| [`PeriodicProfile`](PeriodicProfile.md) | Type | Sinusoidal scalar target; conversion explicitly samples a finite interval. |
| [`MotionEvent`](MotionEvent.md) | Type | Observed sample event; time_s is a recorded time, not a continuous-time proof. |
| [`interpolate_pose`](interpolate_pose.md) | Function | Interpolate position linearly and orientation with shortest-arc SLERP. |

## Module Rules

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.
