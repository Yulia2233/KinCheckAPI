# `ActuatorProfile`

## API Definition

```python
@dataclass(frozen=True)
class ActuatorProfile:
    actuator_id: str
    points: tuple[tuple[float, float], ...]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import ActuatorProfile
```

## Purpose

A time-ordered public effort command, linearly interpolated.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `actuator_id` | `str` | required | Stable, resolvable `actuator_id`. |
| `points` | `tuple[tuple[float, float], ...]` | required | Public input or data field `points`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
