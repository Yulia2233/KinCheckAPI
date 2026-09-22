# Result Packages

Write, validate, and read backend-independent .kincheck motion result packages.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`PACKAGE_SCHEMA_VERSION`](PACKAGE_SCHEMA_VERSION.md) | Constant | Expose the public constant `PACKAGE_SCHEMA_VERSION`. |
| [`DYNAMICS_MEMBER`](DYNAMICS_MEMBER.md) | Constant | Expose the public constant `DYNAMICS_MEMBER`. |
| [`MotionPackage`](MotionPackage.md) | Type | MotionPackage(*, path: 'Path', manifest: 'Mapping[str, Any]', assembly: 'AssemblyModel', motion_result: 'MotionResult', validation: 'Mapping[str, Any]', mesh_members: 'Mapping[str, str]', dynamics_model: 'DynamicsModel | None' = None, static_results: 'tuple[StaticResult, ...]' = (), static_checks: 'tuple[PhysicsReport, ...]' = (), dynamics_history: 'Any | None' = None) |
| [`MotionPackageArtifact`](MotionPackageArtifact.md) | Type | MotionPackageArtifact(*, path: 'Path', sha256: 'str', bytes: 'int', schema_version: 'str', component_count: 'int', trajectory_count: 'int', mesh_count: 'int', missing_mesh_part_ids: 'tuple[str, ...]' = ()) |
| [`export_motion_package`](export_motion_package.md) | Function | Write the assembly, motion result, validation information, and optional meshes to a `.kincheck` file. |
| [`motion_package`](motion_package.md) | Function | Public compatibility alias for `export_motion_package()`. |
| [`read_package`](read_package.md) | Function | Strictly validate and reconstruct a `.kincheck` package; raise `MotionPackageError` on failure. |
| [`validate_package`](validate_package.md) | Function | Validate `.kincheck` member paths, schemas, hashes, and cross-file references and return an aggregate validation result. |

## Module Rules

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.
