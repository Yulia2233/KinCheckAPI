# `ConstraintResidual`

## API Definition

```python
@dataclass(frozen=True)
class ConstraintResidual:
    constraint_id: str
    time_s: float
    position_residual_m: float
    orientation_residual_rad: float
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import ConstraintResidual
```

## Purpose

ConstraintResidual(*, constraint_id: 'str', time_s: 'float', position_residual_m: 'float', orientation_residual_rad: 'float')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `constraint_id` | `str` | required | Stable, resolvable constraint ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `position_residual_m` | `float` | required | `position_residual_m` in metres; finite. |
| `orientation_residual_rad` | `float` | required | `orientation_residual_rad` in radians; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
