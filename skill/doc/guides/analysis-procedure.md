# Kinematic Analysis Procedure

When asked about degrees of freedom, singularities, or reachability, do not run an arbitrary dynamic trajectory.

1. Complete `validate_assembly()` and `validate_topology()`.
2. Use `analyze_dofs()` for structured DOF evidence.
3. Use `solve_position()` for a specified joint pose and `validate_closures()` for closure validation.
4. For a complete `MotionResult`, use `find_singularities()`, `check_reachability()`, `compute_workspace()`, or `trace_connector_path()`.
5. Report analysis samples, reference frames, step sizes, and thresholds; analysis is not a dynamics or strength conclusion.
