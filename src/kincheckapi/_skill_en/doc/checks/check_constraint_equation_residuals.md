# `check_constraint_equation_residuals`

## API Definition

```python
check_constraint_equation_residuals(*, motion_result: MotionResult, constraint_ids: Optional[Sequence[str]] = None, equation_types: Optional[Sequence[Literal['gear', 'belt', 'rack_pinion', 'coupling']]] = None, linear_tolerance_m: float = 1e-08, angular_tolerance_rad: float = 1e-08, start_time_s: float | None = None, end_time_s: float | None = None, disabled_constraint_ids: Sequence[str] = (), check_id: str = 'constraint_equation_residuals') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_constraint_equation_residuals
```

## Purpose

Check signed gear, belt, rack-pinion, and coupling residual samples.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `constraint_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `constraint_ids` collection. |
| `equation_types` | `Optional[Sequence[Literal['gear', 'belt', 'rack_pinion', 'coupling']]]` | `None` | Public input or data field `equation_types`. |
| `linear_tolerance_m` | `float` | `1e-08` | `linear_tolerance_m` in metres; finite. |
| `angular_tolerance_rad` | `float` | `1e-08` | `angular_tolerance_rad` in radians; finite. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `disabled_constraint_ids` | `Sequence[str]` | `()` | Explicitly specified `disabled_constraint_ids` collection. |
| `check_id` | `str` | `'constraint_equation_residuals'` | Stable caller-provided check ID for result traceability. |

## Returns and Failures

Returns `CheckReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Each check must identify its objects, time window, expected value, threshold, and units.
- A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.
- Read `CheckReport.passed` together with evidence, issues, and metadata.
- Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.
- Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.

## Related Documentation

- [`Acceptance Checks`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
