# `solve_contact_dynamics`

## API Definition

```python
solve_contact_dynamics(*, interface: kincheckapi.dynamics_v07.ContactInterface, times_s: Sequence[float], relative_gap_m: Sequence[float], relative_normal_velocity_m_s: Sequence[float]) -> kincheckapi.dynamics_v07.ContactDynamicsResult
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import solve_contact_dynamics
```

## Purpose

Solve the specified kinematic problem: `solve_contact_dynamics`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `interface` | `kincheckapi.dynamics_v07.ContactInterface` | required | Public input or data field `interface`. |
| `times_s` | `Sequence[float]` | required | `times_s` in seconds; finite. |
| `relative_gap_m` | `Sequence[float]` | required | `relative_gap_m` in metres; finite. |
| `relative_normal_velocity_m_s` | `Sequence[float]` | required | `relative_normal_velocity_m_s` in m/s; finite. |

## Returns and Failures

Returns `ContactDynamicsResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
