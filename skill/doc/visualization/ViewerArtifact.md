# `ViewerArtifact`

## API Definition

```python
@dataclass(frozen=True)
class ViewerArtifact:
    root: pathlib.Path
    index_path: pathlib.Path
    manifest_path: pathlib.Path
    component_count: int
    asset_count: int
    missing_asset_component_ids: tuple[str, ...]
```

Source: `src/kincheckapi/visualization.py`.

## Import

```python
from kincheckapi.visualization import ViewerArtifact
```

## Purpose

ViewerArtifact(*, root: 'Path', index_path: 'Path', manifest_path: 'Path', component_count: 'int', asset_count: 'int', missing_asset_component_ids: 'tuple[str, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `root` | `pathlib.Path` | required | Public input or data field `root`. |
| `index_path` | `pathlib.Path` | required | Public input or data field `index_path`. |
| `manifest_path` | `pathlib.Path` | required | Public input or data field `manifest_path`. |
| `component_count` | `int` | required | Public input or data field `component_count`. |
| `asset_count` | `int` | required | Public input or data field `asset_count`. |
| `missing_asset_component_ids` | `tuple[str, ...]` | `()` | Explicitly specified `missing_asset_component_ids` collection. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Visualization consumes only public AssemblyModel and MotionResult data, not private backend state.
- Inspect motion status, recorded trajectories, and mesh assets before export.
- Use the viewer to review evidence, not as a replacement for numerical acceptance checks.

## Related Documentation

- [`Offline Visualization`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
