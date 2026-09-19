# `check_interference`

## API Definition

```python
check_interference(*, assembly: AssemblyModel, motion_result: MotionResult, component_pairs: Optional[Sequence[Sequence[str]]] = None, excluded_pairs: Sequence[Sequence[str]] = (), penetration_tolerance_m: float = 0.0, start_time_s: float | None = None, end_time_s: float | None = None, sampling_scope: Literal['motion_result', 'solver_steps'] = 'motion_result', max_sample_period_s: float | None = None, asset_root: str | pathlib.Path | None = None) -> ClearanceReport
```

Source: `src/kincheckapi/clearance.py`.

## Import

```python
from kincheckapi.clearance import check_interference
```

## Purpose

Check specified component pairs for mesh penetration at discrete motion samples.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_pairs` | `Optional[Sequence[Sequence[str]]]` | `None` | Public input or data field `component_pairs`. |
| `excluded_pairs` | `Sequence[Sequence[str]]` | `()` | Public input or data field `excluded_pairs`. |
| `penetration_tolerance_m` | `float` | `0.0` | `penetration_tolerance_m` in metres; finite. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | Public input or data field `sampling_scope`. |
| `max_sample_period_s` | `float | None` | `None` | `max_sample_period_s` in seconds; finite. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |

## Returns and Failures

Returns `ClearanceReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Discrete interference, minimum-clearance, and envelope results use sampled states; call `check_continuous_interference()` explicitly for cross-sample evidence.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
