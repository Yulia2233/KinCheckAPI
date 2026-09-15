# Kinematic Solving and Analysis

Solve positions and continuous motion and analyze degrees of freedom, Jacobians, singularities, and workspaces.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`KinematicSolveOptions`](KinematicSolveOptions.md) | Type | Deterministic controls for backend integration and constraint solving. |
| [`KinematicCapabilities`](KinematicCapabilities.md) | Type | KinematicCapabilities(*, joint_types: 'Mapping[str, bool]', driver_modes: 'tuple[str, ...]' = ('position', 'speed'), output_channels: 'tuple[str, ...]' = ('joint', 'component', 'connector', 'residuals')) |
| [`ClosureReport`](ClosureReport.md) | Type | ClosureReport(*, passed: 'bool', residuals: 'tuple[Any, ...]' = (), issues: 'tuple[SimIssue, ...]' = ()) |
| [`ConnectorPathResult`](ConnectorPathResult.md) | Type | Path statistics read from one recorded Connector trajectory. |
| [`DofReport`](DofReport.md) | Type | DofReport(*, total_dofs: 'int', joint_dofs: 'Mapping[str, int]', component_dofs: 'Mapping[str, int]', issues: 'tuple[SimIssue, ...]' = ()) |
| [`JacobianOptions`](JacobianOptions.md) | Type | JacobianOptions(*, finite_difference_step: 'float' = 1e-07, rank_tolerance: 'float' = 1e-09) |
| [`JacobianResult`](JacobianResult.md) | Type | JacobianResult(*, target_component_id: 'str', target_connector_id: 'str | None', joint_ids: 'tuple[str, ...]', matrix: 'tuple[tuple[float, ...], ...]', rank: 'int', singular_values: 'tuple[float, ...]', condition_number: 'float | None', units: 'tuple[str, ...]' = ('m/(rad|m)', 'm/(rad|m)', 'm/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)'), issues: 'tuple[SimIssue, ...]' = ()) |
| [`MobilityReport`](MobilityReport.md) | Type | MobilityReport(*, nominal_dofs: 'int', effective_dofs: 'int', joint_dofs: 'Mapping[str, int]', constraint_rank: 'int', constraint_ids: 'tuple[str, ...]' = (), singular_values: 'tuple[float, ...]' = (), issues: 'tuple[SimIssue, ...]' = ()) |
| [`PoseTarget`](PoseTarget.md) | Type | PoseTarget(*, component_id: 'str', pose: 'Pose', connector_id: 'str | None' = None, position_tolerance_m: 'float | None' = None, orientation_tolerance_rad: 'float | None' = None) |
| [`PositionSolveOptions`](PositionSolveOptions.md) | Type | PositionSolveOptions(*, max_iterations: 'int' = 100, position_tolerance_m: 'float' = 1e-07, orientation_tolerance_rad: 'float' = 1e-07, step_tolerance: 'float' = 1e-09, damping: 'float' = 1e-06, finite_difference_step: 'float' = 1e-07, rank_tolerance: 'float' = 1e-09) |
| [`ReachabilityOptions`](ReachabilityOptions.md) | Type | ReachabilityOptions(*, position_tolerance_m: 'float' = 1e-06, orientation_tolerance_rad: 'float' = 1e-06, initial_joint_positions: 'Mapping[str, float]' = <factory>) |
| [`PositionResult`](PositionResult.md) | Type | PositionResult(*, passed: 'bool', joint_positions: 'Mapping[str, float]', component_poses: 'Mapping[str, Any]', residuals: 'tuple[Any, ...]' = (), issues: 'tuple[SimIssue, ...]' = ()) |
| [`ReachabilityResult`](ReachabilityResult.md) | Type | ReachabilityResult(*, reachable: 'bool', target: 'Any', position_result: 'PositionResult | None' = None, issues: 'tuple[SimIssue, ...]' = ()) |
| [`SingularityReport`](SingularityReport.md) | Type | SingularityReport(*, singular_times_s: 'tuple[float, ...]', tolerance: 'float', issues: 'tuple[SimIssue, ...]' = (), samples: 'tuple[Any, ...]' = ()) |
| [`SingularityOptions`](SingularityOptions.md) | Type | Thresholds used by :func:`find_singularities`. |
| [`SingularitySample`](SingularitySample.md) | Type | SingularitySample(*, time_s: 'float', status: 'str', rank: 'int', minimum_singular_value: 'float | None', condition_number: 'float | None', singular_values: 'tuple[float, ...]' = (), joint_positions: 'Mapping[str, float]' = <factory>) |
| [`SolveAttempt`](SolveAttempt.md) | Type | Structured outcome returned by :func:`try_solve_motion`. |
| [`TargetReference`](TargetReference.md) | Type | TargetReference(*, component_id: 'str', connector_id: 'str | None' = None) |
| [`WorkspaceOptions`](WorkspaceOptions.md) | Type | Explicit finite ranges for deterministic workspace sampling. |
| [`WorkspaceResult`](WorkspaceResult.md) | Type | WorkspaceResult(*, target: 'TargetReference', samples: 'tuple[WorkspaceSample, ...]', reachable_points: 'tuple[Pose, ...]', bounds_m: 'Mapping[str, tuple[float, float]]', reachable_fraction: 'float', issues: 'tuple[SimIssue, ...]' = ()) |
| [`WorkspaceSample`](WorkspaceSample.md) | Type | WorkspaceSample(*, joint_positions: 'Mapping[str, float]', reachable: 'bool', pose: 'Pose | None' = None, residual_m: 'float | None' = None, orientation_residual_rad: 'float | None' = None, singularity_status: 'str | None' = None, jacobian_rank: 'int | None' = None, minimum_singular_value: 'float | None' = None, condition_number: 'float | None' = None, issues: 'tuple[SimIssue, ...]' = ()) |
| [`analyze_dofs`](analyze_dofs.md) | Function | Analyze a kinematic property of a mechanism or result: `analyze_dofs`. |
| [`backend_capabilities`](backend_capabilities.md) | Function | Execute the public operation `backend_capabilities`. |
| [`analyze_mobility`](analyze_mobility.md) | Function | Analyze effective mechanism degrees of freedom from nominal joint DOFs and constraint Jacobian rank. |
| [`check_reachability`](check_reachability.md) | Function | Check whether one requested Pose can be satisfied by the assembly. |
| [`compute_workspace`](compute_workspace.md) | Function | Enumerate a finite deterministic set of joint configurations. |
| [`compute_jacobian`](compute_jacobian.md) | Function | Compute a backend-independent six-dimensional finite-difference Jacobian for a component or connector at given joint positions. |
| [`find_singularities`](find_singularities.md) | Function | Compute Jacobian rank, minimum singular value, and condition number at actual MotionResult samples and report singular or near-singular samples. |
| [`solve_motion`](solve_motion.md) | Function | Solve continuous kinematic motion over a Scenario time window and return a backend-independent `MotionResult`. |
| [`solve_position`](solve_position.md) | Function | Solve one kinematic state without starting a time-domain backend. |
| [`trace_connector_path`](trace_connector_path.md) | Function | Compute times, path length, endpoints, and world-coordinate bounds from a recorded connector trajectory. |
| [`try_solve_motion`](try_solve_motion.md) | Function | Retain a structured report and `last_valid_result` after failure; never convert failure into a pass. |
| [`validate_closures`](validate_closures.md) | Function | Validate authored or solved Closure residuals. Calling the compatibility shim without an assembly or result continues to return ``None``. With an assembly, the authored component poses are checked before a solver is started; with a MotionResult, the recorded samples and declared Closure tolerances are checked. |
| [`verify_transmission_ratio`](verify_transmission_ratio.md) | Function | Deprecated compatibility entry point; new code must use `kincheckapi.checks.check_transmission_ratio()`. |
| [`write_motion_result`](write_motion_result.md) | Function | Write a complete public motion result as deterministic JSON. |

## Module Rules

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.
