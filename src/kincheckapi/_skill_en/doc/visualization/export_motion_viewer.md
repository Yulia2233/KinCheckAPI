# `export_motion_viewer`

## API Definition

```python
export_motion_viewer(*, assembly: AssemblyModel, motion_result: MotionResult, output_dir: str | pathlib.Path, asset_root: str | pathlib.Path | None = None, title: str | None = None, input_joint_id: str | None = None, output_joint_id: str | None = None, expected_ratio: float | None = None) -> ViewerArtifact
```

Source: `src/kincheckapi/visualization.py`.

## Import

```python
from kincheckapi.visualization import export_motion_viewer
```

## Purpose

Export motion playback assets for an offline Three.js viewer.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `output_dir` | `str | pathlib.Path` | required | Output directory. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |
| `title` | `str | None` | `None` | Public input or data field `title`. |
| `input_joint_id` | `str | None` | `None` | Stable, resolvable `input_joint_id`. |
| `output_joint_id` | `str | None` | `None` | Stable, resolvable `output_joint_id`. |
| `expected_ratio` | `float | None` | `None` | Positive expected transmission-ratio magnitude; direction is separate. |

## Returns and Failures

Returns `ViewerArtifact`.

## Module Constraints

- Visualization consumes only public AssemblyModel and MotionResult data, not private backend state.
- Inspect motion status, recorded trajectories, and mesh assets before export.
- Use the viewer to review evidence, not as a replacement for numerical acceptance checks.

## Related Documentation

- [`Offline Visualization`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
