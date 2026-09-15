# `DriverTarget`

## API Definition

```python
@dataclass(frozen=True)
class DriverTarget:
    joint_id: str
    time_s: float
    mode: Literal['position', 'speed']
    target: float
    actual: float
    error: float
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import DriverTarget
```

## Purpose

One declared driver target and the corresponding measured joint value.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `mode` | `Literal['position', 'speed']` | required | Public input or data field `mode`. |
| `target` | `float` | required | Public input or data field `target`. |
| `actual` | `float` | required | Public input or data field `actual`. |
| `error` | `float` | required | Public input or data field `error`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
