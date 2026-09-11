# `MotionSummary`

## API Definition

```python
@dataclass(frozen=True)
class MotionSummary:
    status: Literal['completed', 'completed_with_warnings', 'partial']
    duration_s: float
    sample_count: int
    joint_extrema: tuple[JointExtrema, ...]
    maximum_position_residual_m: float
    maximum_orientation_residual_rad: float
    limit_event_count: int
    warning_count: int
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import MotionSummary
```

## Purpose

MotionSummary(*, status: 'MotionStatus', duration_s: 'float', sample_count: 'int', joint_extrema: 'tuple[JointExtrema, ...]', maximum_position_residual_m: 'float', maximum_orientation_residual_rad: 'float', limit_event_count: 'int', warning_count: 'int')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `status` | `Literal['completed', 'completed_with_warnings', 'partial']` | required | Structured status interpreted according to the stable values for the result type. |
| `duration_s` | `float` | required | Total run duration in seconds; finite and positive. |
| `sample_count` | `int` | required | Public input or data field `sample_count`. |
| `joint_extrema` | `tuple[JointExtrema, ...]` | required | Public input or data field `joint_extrema`. |
| `maximum_position_residual_m` | `float` | required | `maximum_position_residual_m` in metres; finite. |
| `maximum_orientation_residual_rad` | `float` | required | `maximum_orientation_residual_rad` in radians; finite. |
| `limit_event_count` | `int` | required | Public input or data field `limit_event_count`. |
| `warning_count` | `int` | required | Public input or data field `warning_count`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
