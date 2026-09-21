# `summarize_drive_duty`

## API Definition

```python
summarize_drive_duty(*, times_s: Sequence[float], torque_nm: Sequence[float], speed_rad_s: Sequence[float]) -> kincheckapi.fatigue.DriveDutySummary
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import summarize_drive_duty
```

## Purpose

Execute the public operation `summarize_drive_duty`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `times_s` | `Sequence[float]` | required | `times_s` in seconds; finite. |
| `torque_nm` | `Sequence[float]` | required | Public input or data field `torque_nm`. |
| `speed_rad_s` | `Sequence[float]` | required | `speed_rad_s` in rad/s; finite. |

## Returns and Failures

Returns `DriveDutySummary`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
