# `ForwardDynamicsRequest`

## API Definition

```python
@dataclass(frozen=True)
class ForwardDynamicsRequest:
    initial_states: tuple[kincheckapi.dynamic_types.DynamicState, ...]
    actuators: tuple[kincheckapi.dynamic_types.ActuatorSpec, ...]
    profiles: tuple[kincheckapi.dynamic_types.ActuatorProfile, ...]
    duration_s: float
    sample_period_s: float
    gravity: kincheckapi.physics_types.GravityField
    loads: tuple[kincheckapi.physics_types.WrenchLoad, ...]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import ForwardDynamicsRequest
```

## Purpose

Inputs for finite-actuator forward integration.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `initial_states` | `tuple[kincheckapi.dynamic_types.DynamicState, ...]` | required | Public input or data field `initial_states`. |
| `actuators` | `tuple[kincheckapi.dynamic_types.ActuatorSpec, ...]` | required | Public input or data field `actuators`. |
| `profiles` | `tuple[kincheckapi.dynamic_types.ActuatorProfile, ...]` | required | Public input or data field `profiles`. |
| `duration_s` | `float` | required | Total run duration in seconds; finite and positive. |
| `sample_period_s` | `float` | required | `sample_period_s` in seconds; finite. |
| `gravity` | `kincheckapi.physics_types.GravityField` | default_factory | Public input or data field `gravity`. |
| `loads` | `tuple[kincheckapi.physics_types.WrenchLoad, ...]` | `()` | Public input or data field `loads`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
