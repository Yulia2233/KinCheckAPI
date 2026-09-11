# `InterferenceEvent`

## API Definition

```python
@dataclass(frozen=True)
class InterferenceEvent:
    component_a_id: str
    component_b_id: str
    time_s: float
    penetration_depth_m: float
    position_m: tuple[float, float, float] | None
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import InterferenceEvent
```

## Purpose

InterferenceEvent(*, component_a_id: 'str', component_b_id: 'str', time_s: 'float', penetration_depth_m: 'float', position_m: 'Vector3 | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_a_id` | `str` | required | Stable, resolvable `component_a_id`. |
| `component_b_id` | `str` | required | Stable, resolvable `component_b_id`. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `penetration_depth_m` | `float` | required | `penetration_depth_m` in metres; finite. |
| `position_m` | `tuple[float, float, float] | None` | `None` | `position_m` in metres; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
