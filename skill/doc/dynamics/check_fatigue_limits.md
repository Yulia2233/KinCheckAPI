# `check_fatigue_limits`

## API Definition

```python
check_fatigue_limits(*, result: kincheckapi.fatigue.FatigueReport, allowable_damage: float | None = None) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import check_fatigue_limits
```

## Purpose

Execute a structured check: `check_fatigue_limits`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.fatigue.FatigueReport` | required | Public input or data field `result`. |
| `allowable_damage` | `float | None` | `None` | Public input or data field `allowable_damage`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
