# `write_motion_result`

## API Definition

```python
write_motion_result(*, motion_result: MotionResult, path: str | pathlib.Path) -> None
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import write_motion_result
```

## Purpose

Write a complete public motion result as deterministic JSON.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `path` | `str | pathlib.Path` | required | Input or output path as described by the operation. |

## Returns and Failures

Returns `None`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
