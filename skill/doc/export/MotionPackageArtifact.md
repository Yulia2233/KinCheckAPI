# `MotionPackageArtifact`

## API Definition

```python
@dataclass(frozen=True)
class MotionPackageArtifact:
    path: pathlib.Path
    sha256: str
    bytes: int
    schema_version: str
    component_count: int
    trajectory_count: int
    mesh_count: int
    missing_mesh_part_ids: tuple[str, ...]
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import MotionPackageArtifact
```

## Purpose

MotionPackageArtifact(*, path: 'Path', sha256: 'str', bytes: 'int', schema_version: 'str', component_count: 'int', trajectory_count: 'int', mesh_count: 'int', missing_mesh_part_ids: 'tuple[str, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | `pathlib.Path` | required | Input or output path as described by the operation. |
| `sha256` | `str` | required | Public input or data field `sha256`. |
| `bytes` | `int` | required | Public input or data field `bytes`. |
| `schema_version` | `str` | required | Public input or data field `schema_version`. |
| `component_count` | `int` | required | Public input or data field `component_count`. |
| `trajectory_count` | `int` | required | Public input or data field `trajectory_count`. |
| `mesh_count` | `int` | required | Public input or data field `mesh_count`. |
| `missing_mesh_part_ids` | `tuple[str, ...]` | `()` | Explicitly specified `missing_mesh_part_ids` collection. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
