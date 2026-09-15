# `DriverTrajectory`

## API Definition

```python
@dataclass(frozen=True)
class DriverTrajectory:
    joint_id: str
    mode: Literal['position', 'speed']
    samples: tuple[DriverTarget, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import DriverTrajectory
```

## Purpose

Time ordered target/actual records for one joint driver.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `mode` | `Literal['position', 'speed']` | required | Public input or data field `mode`. |
| `samples` | `tuple[DriverTarget, ...]` | required | Public input or data field `samples`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
