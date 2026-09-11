# Result Models and Queries

Read status, trajectories, residuals, and event evidence from MotionResult objects.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`ComponentState`](ComponentState.md) | Type | ComponentState(*, component_id: 'str', time_s: 'float', pose: 'Pose', linear_velocity_m_s: 'Vector3 | None' = None, angular_velocity_rad_s: 'Vector3 | None' = None, linear_acceleration_m_s2: 'Vector3 | None' = None, angular_acceleration_rad_s2: 'Vector3 | None' = None) |
| [`ConnectorState`](ConnectorState.md) | Type | ConnectorState(*, component_id: 'str', connector_id: 'str', time_s: 'float', pose: 'Pose', linear_velocity_m_s: 'Vector3 | None' = None, angular_velocity_rad_s: 'Vector3 | None' = None, linear_acceleration_m_s2: 'Vector3 | None' = None, angular_acceleration_rad_s2: 'Vector3 | None' = None) |
| [`ConstraintResidual`](ConstraintResidual.md) | Type | ConstraintResidual(*, constraint_id: 'str', time_s: 'float', position_residual_m: 'float', orientation_residual_rad: 'float') |
| [`ConstraintEquationResidual`](ConstraintEquationResidual.md) | Type | Signed residual of a gear, belt, rack-pinion, or coupling equation. |
| [`ConstraintEquationType`](ConstraintEquationType.md) | Type alias | Define the public type contract used by `ConstraintEquationType`. |
| [`ConstraintEquationUnit`](ConstraintEquationUnit.md) | Type alias | Define the public type contract used by `ConstraintEquationUnit`. |
| [`Direction`](Direction.md) | Type alias | Define the public type contract used by `Direction`. |
| [`InterferenceEvent`](InterferenceEvent.md) | Type | InterferenceEvent(*, component_a_id: 'str', component_b_id: 'str', time_s: 'float', penetration_depth_m: 'float', position_m: 'Vector3 | None' = None) |
| [`InterferenceResult`](InterferenceResult.md) | Type | InterferenceResult(*, events: 'tuple[InterferenceEvent, ...]' = ()) |
| [`JointExtrema`](JointExtrema.md) | Type | JointExtrema(*, joint_id: 'str', minimum_position: 'float', maximum_position: 'float', maximum_absolute_velocity: 'float', maximum_absolute_acceleration: 'float') |
| [`JointState`](JointState.md) | Type | One scalar joint sample in SI units (radians or metres). |
| [`JointTrajectory`](JointTrajectory.md) | Type | Complete sampled state of one revolute or prismatic joint. |
| [`LimitEvent`](LimitEvent.md) | Type | LimitEvent(*, joint_id: 'str', time_s: 'float', side: 'LimitSide', event_type: 'LimitEventType', position: 'float', limit_position: 'float') |
| [`MotionResult`](MotionResult.md) | Type | Stable output of any KinCheckAPI motion backend. |
| [`MotionStatus`](MotionStatus.md) | Type alias | Define the public type contract used by `MotionStatus`. |
| [`MotionSummary`](MotionSummary.md) | Type | MotionSummary(*, status: 'MotionStatus', duration_s: 'float', sample_count: 'int', joint_extrema: 'tuple[JointExtrema, ...]', maximum_position_residual_m: 'float', maximum_orientation_residual_rad: 'float', limit_event_count: 'int', warning_count: 'int') |
| [`Trajectory`](Trajectory.md) | Type | Rigid-body trajectory for a component or one of its connectors. |
| [`TransmissionRatioCheck`](TransmissionRatioCheck.md) | Type | TransmissionRatioCheck(*, passed: 'bool', expected_ratio: 'float', measured_ratio: 'float | None', relative_error: 'float | None', expected_direction: 'Direction', measured_direction: 'Direction | None', input_joint_id: 'str', output_joint_id: 'str', input_member: 'str | None' = None, output_member: 'str | None' = None, fixed_member: 'str | None' = None, sample_count: 'int' = 0, rejected_sample_count: 'int' = 0, start_time_s: 'float | None' = None, end_time_s: 'float | None' = None, stage_checks: 'tuple[_PlanetaryStageEvidence, ...]' = (), evidence: 'tuple[Evidence, ...]' = (), issues: 'tuple[SimIssue, ...]' = ()) |
| [`list_constraint_residuals`](list_constraint_residuals.md) | Function | Filter and return recorded structured evidence: `list_constraint_residuals`. |
| [`list_constraint_equation_residuals`](list_constraint_equation_residuals.md) | Function | Filter and return recorded structured evidence: `list_constraint_equation_residuals`. |
| [`list_interference_events`](list_interference_events.md) | Function | Filter and return recorded structured evidence: `list_interference_events`. |
| [`list_limit_events`](list_limit_events.md) | Function | Filter and return recorded structured evidence: `list_limit_events`. |
| [`read_component_pose`](read_component_pose.md) | Function | Read or interpolate a component world pose at a specified time. |
| [`read_component_state`](read_component_state.md) | Function | Read a component world pose and the available linear and angular motion values. |
| [`read_connector_state`](read_connector_state.md) | Function | Read a specified connector world pose and available spatial motion state. |
| [`read_joint_state`](read_joint_state.md) | Function | Read or interpolate joint position, velocity, and acceleration at a specified time. |
| [`read_trajectory`](read_trajectory.md) | Function | Return a complete component or connector trajectory already recorded in the result. |
| [`summarize_motion`](summarize_motion.md) | Function | Summarize status, duration, sample count, joint extrema, maximum residuals, and event counts. |
| [`write_motion_result`](write_motion_result.md) | Function | Write a complete public motion result as deterministic JSON. |

## Module Rules

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.
