# `list_constraint_equation_residuals`

## API Definition

```python
list_constraint_equation_residuals(*, motion_result: MotionResult, constraint_id: str | None = None) -> tuple[ConstraintEquationResidual, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import list_constraint_equation_residuals
```

## Purpose

Filter and return recorded structured evidence: `list_constraint_equation_residuals`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `constraint_id` | `str | None` | `None` | Stable, resolvable constraint ID. |

## Returns and Failures

Returns `tuple[ConstraintEquationResidual, ...]`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
