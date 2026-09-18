# `PeriodicProfile`

## API Definition

```python
@dataclass(frozen=True)
class PeriodicProfile:
    period_s: float
    amplitude: float
    offset: float
    phase_rad: float
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import PeriodicProfile
```

## Purpose

Sinusoidal scalar target; conversion explicitly samples a finite interval.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `period_s` | `float` | required | Sampling period in seconds; finite and positive. |
| `amplitude` | `float` | required | Public input or data field `amplitude`. |
| `offset` | `float` | `0.0` | Public input or data field `offset`. |
| `phase_rad` | `float` | `0.0` | `phase_rad` in radians; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
