# `BrakePolicy`

## API Definition

```python
@dataclass(frozen=True)
class BrakePolicy:
    policy_id: str
    trigger_time_s: float
    braking_limits: Mapping[str, float]
    delay_s: float
    hold_after_stop: bool
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import BrakePolicy
```

## Purpose

BrakePolicy(*, policy_id: 'str', trigger_time_s: 'float', braking_limits: 'Mapping[str, float]', delay_s: 'float' = 0.0, hold_after_stop: 'bool' = True)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `policy_id` | `str` | required | Stable, resolvable `policy_id`. |
| `trigger_time_s` | `float` | required | `trigger_time_s` in seconds; finite. |
| `braking_limits` | `Mapping[str, float]` | required | Public input or data field `braking_limits`. |
| `delay_s` | `float` | `0.0` | `delay_s` in seconds; finite. |
| `hold_after_stop` | `bool` | `True` | Public input or data field `hold_after_stop`. |

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
