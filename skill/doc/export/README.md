# Result Packages

Write, validate, and read backend-independent .kincheck motion result packages.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`PACKAGE_SCHEMA_VERSION`](PACKAGE_SCHEMA_VERSION.md) | Constant | str(object='') -> str str(bytes_or_buffer[, encoding[, errors]]) -> str Create a new string object from the given object. If encoding or errors is specified, then the object must expose a data buffer that will be decoded using the given encoding and error handler. Otherwise, returns the result of object.__str__() (if defined) or repr(object). encoding defaults to sys.getdefaultencoding(). errors defaults to 'strict'. |
| [`MotionPackage`](MotionPackage.md) | Type | MotionPackage(*, path: 'Path', manifest: 'Mapping[str, Any]', assembly: 'AssemblyModel', motion_result: 'MotionResult', validation: 'Mapping[str, Any]', mesh_members: 'Mapping[str, str]') |
| [`MotionPackageArtifact`](MotionPackageArtifact.md) | Type | MotionPackageArtifact(*, path: 'Path', sha256: 'str', bytes: 'int', schema_version: 'str', component_count: 'int', trajectory_count: 'int', mesh_count: 'int', missing_mesh_part_ids: 'tuple[str, ...]' = ()) |
| [`export_motion_package`](export_motion_package.md) | Function | Write the assembly, motion result, validation information, and optional meshes to a `.kincheck` file. |
| [`motion_package`](motion_package.md) | Function | Public compatibility alias for `export_motion_package()`. |
| [`read_package`](read_package.md) | Function | Strictly validate and reconstruct a `.kincheck` package; raise `MotionPackageError` on failure. |
| [`validate_package`](validate_package.md) | Function | Validate `.kincheck` member paths, schemas, hashes, and cross-file references and return an aggregate validation result. |

## Module Rules

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.
