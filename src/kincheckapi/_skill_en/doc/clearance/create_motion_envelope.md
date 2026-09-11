# `create_motion_envelope`

## API Definition

```python
create_motion_envelope(*, assembly: AssemblyModel, motion_result: MotionResult, component_ids: Optional[Sequence[str]] = None, start_time_s: float | None = None, end_time_s: float | None = None, sampling_scope: Literal['motion_result', 'solver_steps'] = 'motion_result', asset_root: str | pathlib.Path | None = None) -> ClearanceReport
```

Source: `src/kincheckapi/clearance.py`.

## Import

```python
from kincheckapi.clearance import create_motion_envelope
```

## Purpose

Create a discrete motion envelope for specified components for later spatial interference analysis.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `component_ids` collection. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | Public input or data field `sampling_scope`. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |

## Returns and Failures

Returns `ClearanceReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Results come from triangle meshes and discrete time samples; they are not continuous-time collision proofs.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
