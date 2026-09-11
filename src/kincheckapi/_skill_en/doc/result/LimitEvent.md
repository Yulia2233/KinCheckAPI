# `LimitEvent`

## API Definition

```python
@dataclass(frozen=True)
class LimitEvent:
    joint_id: str
    time_s: float
    side: Literal['lower', 'upper']
    event_type: Literal['reached', 'exceeded']
    position: float
    limit_position: float
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import LimitEvent
```

## Purpose

LimitEvent(*, joint_id: 'str', time_s: 'float', side: 'LimitSide', event_type: 'LimitEventType', position: 'float', limit_position: 'float')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `side` | `Literal['lower', 'upper']` | required | Public input or data field `side`. |
| `event_type` | `Literal['reached', 'exceeded']` | required | Public input or data field `event_type`. |
| `position` | `float` | required | Public input or data field `position`. |
| `limit_position` | `float` | required | Public input or data field `limit_position`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
