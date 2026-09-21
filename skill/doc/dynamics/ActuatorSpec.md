# `ActuatorSpec`

## API Definition

```python
@dataclass(frozen=True)
class ActuatorSpec:
    actuator_id: str
    joint_id: str
    max_effort: float
    max_speed: float | None
    efficiency: float
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import ActuatorSpec
```

## Purpose

A finite ideal torque/force actuator bound to one scalar Joint.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `actuator_id` | `str` | required | Stable, resolvable `actuator_id`. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `max_effort` | `float` | required | Public input or data field `max_effort`. |
| `max_speed` | `float | None` | `None` | Public input or data field `max_speed`. |
| `efficiency` | `float` | `1.0` | Public input or data field `efficiency`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
