# `ContactEvent`

## API Definition

```python
@dataclass(frozen=True)
class ContactEvent:
    time_s: float
    contact_id: str
    state: str
    normal_force_n: float
    tangential_force_n: tuple[float, float, float]
    penetration_m: float
    normal_impulse_ns: float
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ContactEvent
```

## Purpose

ContactEvent(*, time_s: 'float', contact_id: 'str', state: 'str', normal_force_n: 'float', tangential_force_n: 'tuple[float, float, float]', penetration_m: 'float', normal_impulse_ns: 'float' = 0.0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `contact_id` | `str` | required | Stable, resolvable `contact_id`. |
| `state` | `str` | required | Public input or data field `state`. |
| `normal_force_n` | `float` | required | Public input or data field `normal_force_n`. |
| `tangential_force_n` | `tuple[float, float, float]` | required | Public input or data field `tangential_force_n`. |
| `penetration_m` | `float` | required | `penetration_m` in metres; finite. |
| `normal_impulse_ns` | `float` | `0.0` | Public input or data field `normal_impulse_ns`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
