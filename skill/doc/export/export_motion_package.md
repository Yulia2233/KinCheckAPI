# `export_motion_package`

## API Definition

```python
export_motion_package(*, assembly: AssemblyModel, motion_result: MotionResult, output_path: str | pathlib.Path, asset_root: str | pathlib.Path | None = None, title: str | None = None, require_meshes: bool = False, metadata: Optional[Mapping[str, Any]] = None, dynamics_model: kincheckapi.physics_types.DynamicsModel | None = None, static_results: tuple[kincheckapi.physics_types.StaticResult, ...] = (), static_checks: tuple[kincheckapi.physics_types.PhysicsReport, ...] = (), dynamics_history: typing.Any | None = None) -> MotionPackageArtifact
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import export_motion_package
```

## Purpose

Write the assembly, motion result, validation information, and optional meshes to a `.kincheck` file.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `output_path` | `str | pathlib.Path` | required | Output file path. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |
| `title` | `str | None` | `None` | Public input or data field `title`. |
| `require_meshes` | `bool` | `False` | Public input or data field `require_meshes`. |
| `metadata` | `Optional[Mapping[str, Any]]` | `None` | Additional read-only structured metadata. |
| `dynamics_model` | `kincheckapi.physics_types.DynamicsModel | None` | `None` | Public input or data field `dynamics_model`. |
| `static_results` | `tuple[kincheckapi.physics_types.StaticResult, ...]` | `()` | Public input or data field `static_results`. |
| `static_checks` | `tuple[kincheckapi.physics_types.PhysicsReport, ...]` | `()` | Public input or data field `static_checks`. |
| `dynamics_history` | `Any | None` | `None` | Public input or data field `dynamics_history`. |

## Returns and Failures

Returns `MotionPackageArtifact`.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
