# Acceptance Checks

Turn user claims into structured, reviewable kinematic acceptance checks.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`CheckReport`](CheckReport.md) | Type | One deterministic, machine-readable verification outcome. |
| [`CheckSpec`](CheckSpec.md) | Type | Explicit instruction consumed by :func:`run_checks`. |
| [`CheckSuiteReport`](CheckSuiteReport.md) | Type | Ordered aggregate returned by :func:`run_checks`. |
| [`DriverTrackingReport`](DriverTrackingReport.md) | Type | Acceptance evidence comparing declared driver targets with actual samples. |
| [`CheckType`](CheckType.md) | Type alias | Define the public type contract used by `CheckType`. |
| [`Direction`](Direction.md) | Type alias | Define the public type contract used by `Direction`. |
| [`RatioMeasurement`](RatioMeasurement.md) | Type alias | Define the public type contract used by `RatioMeasurement`. |
| [`AssemblyIntegrityReport`](AssemblyIntegrityReport.md) | Type | Structured result for whole-assembly connectivity over checked states. |
| [`ContainmentRelation`](ContainmentRelation.md) | Type | A declared relative-axis interval that keeps one component contained. |
| [`IntegrityRelationResult`](IntegrityRelationResult.md) | Type | One relation observation at one checked state. |
| [`check_assembly_integrity`](check_assembly_integrity.md) | Function | Check that Components remain one connected assembly at every static or MotionResult sample and report disconnection, detachment, or escape. |
| [`check_constraint_equation_residuals`](check_constraint_equation_residuals.md) | Function | Check signed gear, belt, rack-pinion, and coupling residual samples. |
| [`check_constraint_residuals`](check_constraint_residuals.md) | Function | Check sampled constraint and, by default, closure residuals. |
| [`check_driver_tracking`](check_driver_tracking.md) | Function | Compare one declared position/speed driver to the recorded trajectory. |
| [`check_joint_limits`](check_joint_limits.md) | Function | Verify sampled joint positions against authored assembly limits. |
| [`check_interference`](check_interference.md) | Function | Check specified component pairs for mesh penetration at discrete motion samples. |
| [`check_minimum_clearance`](check_minimum_clearance.md) | Function | Run the strict signed minimum-clearance check as a CheckReport. |
| [`check_motion_envelope`](check_motion_envelope.md) | Function | Compute a mesh motion envelope and expose it through the check API. |
| [`check_pose_target`](check_pose_target.md) | Function | Check recorded component/Connector poses against explicit targets. |
| [`check_trajectory`](check_trajectory.md) | Function | Check sampled trajectory ranges without modifying the result. |
| [`check_transmission_ratio`](check_transmission_ratio.md) | Function | Compare two explicit joint curves after deterministic time alignment. |
| [`run_checks`](run_checks.md) | Function | Execute explicit acceptance claims in `CheckSpec` order and return a `CheckSuiteReport`. |

## Module Rules

- Each check must identify its objects, time window, expected value, threshold, and units.
- A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.
- Read `CheckReport.passed` together with evidence, issues, and metadata.
- Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.
- Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.
