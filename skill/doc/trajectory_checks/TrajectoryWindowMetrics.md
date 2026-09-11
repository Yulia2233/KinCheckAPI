# `TrajectoryWindowMetrics`

## API Definition

```python
@dataclass(frozen=True)
class TrajectoryWindowMetrics:
    indices: tuple[int, ...]
    path_length_m: float
    bounds_m: Mapping[str, tuple[float, float]]
```

Source: `src/kincheckapi/trajectory_checks.py`.

## Import

```python
from kincheckapi.trajectory_checks import TrajectoryWindowMetrics
```

## Purpose

TrajectoryWindowMetrics(*, indices: 'tuple[int, ...]', path_length_m: 'float', bounds_m: 'Mapping[str, tuple[float, float]]')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `indices` | `tuple[int, ...]` | required | Public input or data field `indices`. |
| `path_length_m` | `float` | required | `path_length_m` in metres; finite. |
| `bounds_m` | `Mapping[str, tuple[float, float]]` | required | `bounds_m` in metres; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The time window must lie in the actual sample range and contain enough samples.
- Do not interpret empty windows or invalid position bounds as a pass.
- Path length and bounds are derived from discrete samples.

## Related Documentation

- [`Trajectory Utilities`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
