# `MultibodySample`

## API Definition

```python
@dataclass(frozen=True)
class MultibodySample:
    time_s: float
    positions: Mapping[str, float]
    velocities: Mapping[str, float]
    accelerations: Mapping[str, float]
    generalized_forces: Mapping[str, float]
    constraint_reactions: Mapping[str, float]
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import MultibodySample
```

## Purpose

MultibodySample(*, time_s: 'float', positions: 'Mapping[str, float]', velocities: 'Mapping[str, float]', accelerations: 'Mapping[str, float]', generalized_forces: 'Mapping[str, float]', constraint_reactions: 'Mapping[str, float]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `positions` | `Mapping[str, float]` | required | Public input or data field `positions`. |
| `velocities` | `Mapping[str, float]` | required | Public input or data field `velocities`. |
| `accelerations` | `Mapping[str, float]` | required | Public input or data field `accelerations`. |
| `generalized_forces` | `Mapping[str, float]` | required | Public input or data field `generalized_forces`. |
| `constraint_reactions` | `Mapping[str, float]` | default_factory | Public input or data field `constraint_reactions`. |

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
