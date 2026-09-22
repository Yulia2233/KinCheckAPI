# `ActuatorEnvelope`

## API Definition

```python
@dataclass(frozen=True)
class ActuatorEnvelope:
    envelope_id: str
    dof_limits: Mapping[str, float]
    velocity_limits: Mapping[str, float]
    power_limit_w: float | None
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ActuatorEnvelope
```

## Purpose

Force/velocity envelope used for post-solve rigid-body acceptance checks.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `envelope_id` | `str` | required | Stable, resolvable `envelope_id`. |
| `dof_limits` | `Mapping[str, float]` | required | Public input or data field `dof_limits`. |
| `velocity_limits` | `Mapping[str, float]` | default_factory | Public input or data field `velocity_limits`. |
| `power_limit_w` | `float | None` | `None` | Public input or data field `power_limit_w`. |
| `source` | `str` | `'declared'` | Public input or data field `source`. |

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
