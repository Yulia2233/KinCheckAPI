# `check_contact_convergence`

## API Definition

```python
check_contact_convergence(*, results_by_step: Mapping[float, kincheckapi.dynamics_v07.ContactDynamicsResult], relative_tolerance: float = 0.05) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import check_contact_convergence
```

## Purpose

Compare contact impulse and penetration across declared time-step runs.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `results_by_step` | `Mapping[float, kincheckapi.dynamics_v07.ContactDynamicsResult]` | required | Public input or data field `results_by_step`. |
| `relative_tolerance` | `float` | `0.05` | Public input or data field `relative_tolerance`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
