# `MotionPackage`

## API Definition

```python
@dataclass(frozen=True)
class MotionPackage:
    path: pathlib.Path
    manifest: Mapping[str, Any]
    assembly: AssemblyModel
    motion_result: MotionResult
    validation: Mapping[str, Any]
    mesh_members: Mapping[str, str]
    dynamics_model: kincheckapi.physics_types.DynamicsModel | None
    static_results: tuple[kincheckapi.physics_types.StaticResult, ...]
    static_checks: tuple[kincheckapi.physics_types.PhysicsReport, ...]
    dynamics_history: Any | None
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import MotionPackage
```

## Purpose

MotionPackage(*, path: 'Path', manifest: 'Mapping[str, Any]', assembly: 'AssemblyModel', motion_result: 'MotionResult', validation: 'Mapping[str, Any]', mesh_members: 'Mapping[str, str]', dynamics_model: 'DynamicsModel | None' = None, static_results: 'tuple[StaticResult, ...]' = (), static_checks: 'tuple[PhysicsReport, ...]' = (), dynamics_history: 'Any | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | `pathlib.Path` | required | Input or output path as described by the operation. |
| `manifest` | `Mapping[str, Any]` | required | Public input or data field `manifest`. |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `validation` | `Mapping[str, Any]` | required | Public input or data field `validation`. |
| `mesh_members` | `Mapping[str, str]` | required | Public input or data field `mesh_members`. |
| `dynamics_model` | `kincheckapi.physics_types.DynamicsModel | None` | `None` | Public input or data field `dynamics_model`. |
| `static_results` | `tuple[kincheckapi.physics_types.StaticResult, ...]` | `()` | Public input or data field `static_results`. |
| `static_checks` | `tuple[kincheckapi.physics_types.PhysicsReport, ...]` | `()` | Public input or data field `static_checks`. |
| `dynamics_history` | `Any | None` | `None` | Public input or data field `dynamics_history`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
