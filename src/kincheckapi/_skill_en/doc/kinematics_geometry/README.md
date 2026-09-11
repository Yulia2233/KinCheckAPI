# Low-Level Kinematic Geometry

Provide backend-independent pose propagation, Jacobian, mobility, and position-solving primitives.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`JacobianOptions`](JacobianOptions.md) | Type | JacobianOptions(*, finite_difference_step: 'float' = 1e-07, rank_tolerance: 'float' = 1e-09) |
| [`JacobianResult`](JacobianResult.md) | Type | JacobianResult(*, target_component_id: 'str', target_connector_id: 'str | None', joint_ids: 'tuple[str, ...]', matrix: 'tuple[tuple[float, ...], ...]', rank: 'int', singular_values: 'tuple[float, ...]', condition_number: 'float | None', units: 'tuple[str, ...]' = ('m/(rad|m)', 'm/(rad|m)', 'm/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)'), issues: 'tuple[SimIssue, ...]' = ()) |
| [`MobilityReport`](MobilityReport.md) | Type | MobilityReport(*, nominal_dofs: 'int', effective_dofs: 'int', joint_dofs: 'Mapping[str, int]', constraint_rank: 'int', constraint_ids: 'tuple[str, ...]' = (), singular_values: 'tuple[float, ...]' = (), issues: 'tuple[SimIssue, ...]' = ()) |
| [`PoseTarget`](PoseTarget.md) | Type | PoseTarget(*, component_id: 'str', pose: 'Pose', connector_id: 'str | None' = None, position_tolerance_m: 'float | None' = None, orientation_tolerance_rad: 'float | None' = None) |
| [`PositionSolveOptions`](PositionSolveOptions.md) | Type | PositionSolveOptions(*, max_iterations: 'int' = 100, position_tolerance_m: 'float' = 1e-07, orientation_tolerance_rad: 'float' = 1e-07, step_tolerance: 'float' = 1e-09, damping: 'float' = 1e-06, finite_difference_step: 'float' = 1e-07, rank_tolerance: 'float' = 1e-09) |
| [`analyze_mobility`](analyze_mobility.md) | Function | Analyze effective mechanism degrees of freedom from nominal joint DOFs and constraint Jacobian rank. |
| [`compute_jacobian`](compute_jacobian.md) | Function | Compute a backend-independent six-dimensional finite-difference Jacobian for a component or connector at given joint positions. |
| [`forward_component_poses`](forward_component_poses.md) | Function | Propagate world poses for all components from the assembly tree and joint positions. |
| [`forward_connector_poses`](forward_connector_poses.md) | Function | Propagate world poses for all connectors from the assembly tree and joint positions. |
| [`solve_position_core`](solve_position_core.md) | Function | Solve one authored assembly pose and return backend-neutral records. |

## Module Rules

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.
