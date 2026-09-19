# `check_continuous_interference`

## API Definition

```python
check_continuous_interference(*, assembly: AssemblyModel, motion_result: MotionResult, component_pairs: Sequence[Sequence[str]], options: Union[ContinuousInterferenceOptions, Mapping[str, Any], NoneType] = None, start_time_s: float | None = None, end_time_s: float | None = None, asset_root: str | pathlib.Path | None = None) -> ContinuousInterferenceReport
```

Source: `src/kincheckapi/clearance.py`.

## Import

```python
from kincheckapi.clearance import check_continuous_interference
```

## Purpose

Conservative continuous collision check over piecewise rigid intervals.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_pairs` | `Sequence[Sequence[str]]` | required | Public input or data field `component_pairs`. |
| `options` | `Union[ContinuousInterferenceOptions, Mapping[str, Any], NoneType]` | `None` | Public solve or analysis options; record the effective thresholds. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |

## Returns and Failures

Returns `ContinuousInterferenceReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Discrete interference, minimum-clearance, and envelope results use sampled states; call `check_continuous_interference()` explicitly for cross-sample evidence.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
