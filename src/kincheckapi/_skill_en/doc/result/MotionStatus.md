# `MotionStatus`

## API Definition

```python
MotionStatus = Literal
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import MotionStatus
```

## Purpose

Define the public type contract used by `MotionStatus`.

## Returns and Failures

This is a type contract, not a callable function.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
