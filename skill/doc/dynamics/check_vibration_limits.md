# `check_vibration_limits`

## API Definition

```python
check_vibration_limits(*, values: Sequence[float], limit: float, metric: str = 'peak', unit: str = '') -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import check_vibration_limits
```

## Purpose

Execute a structured check: `check_vibration_limits`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `values` | `Sequence[float]` | required | Public input or data field `values`. |
| `limit` | `float` | required | Public input or data field `limit`. |
| `metric` | `str` | `'peak'` | Public input or data field `metric`. |
| `unit` | `str` | `''` | Public input or data field `unit`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
