# `summarize_motion`

## API Definition

```python
summarize_motion(*, motion_result: MotionResult) -> MotionSummary
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import summarize_motion
```

## Purpose

Summarize status, duration, sample count, joint extrema, maximum residuals, and event counts.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |

## Returns and Failures

Returns `MotionSummary`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
