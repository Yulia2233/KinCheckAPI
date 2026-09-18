# `record_verification_reports`

## API Definition

```python
record_verification_reports(*, motion_result: MotionResult, reports: Sequence[Any]) -> MotionResult
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import record_verification_reports
```

## Purpose

Attach immutable check evidence without changing solver completion status.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `reports` | `Sequence[Any]` | required | Public input or data field `reports`. |

## Returns and Failures

Returns `MotionResult`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
