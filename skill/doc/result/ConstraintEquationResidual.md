# `ConstraintEquationResidual`

## API Definition

```python
@dataclass(frozen=True)
class ConstraintEquationResidual:
    constraint_id: str
    time_s: float
    value: float
    absolute_value: float | None
    unit: Literal['m', 'rad']
    equation_type: Literal['gear', 'belt', 'rack_pinion', 'coupling']
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import ConstraintEquationResidual
```

## Purpose

Signed residual of a gear, belt, rack-pinion, or coupling equation.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `constraint_id` | `str` | required | Stable, resolvable constraint ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `value` | `float` | required | Public input or data field `value`. |
| `absolute_value` | `float | None` | `None` | Public input or data field `absolute_value`. |
| `unit` | `Literal['m', 'rad']` | required | Public input or data field `unit`. |
| `equation_type` | `Literal['gear', 'belt', 'rack_pinion', 'coupling']` | required | Public input or data field `equation_type`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
