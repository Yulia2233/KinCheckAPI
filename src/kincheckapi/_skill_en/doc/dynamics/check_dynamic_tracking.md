# `check_dynamic_tracking`

## API Definition

```python
check_dynamic_tracking(*, result: kincheckapi.dynamic_types.ForwardDynamicsResult, targets: Mapping[str, float], tolerance: Union[Mapping[str, float], float] = 0.001) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/dynamic_solver.py`.

## Import

```python
from kincheckapi.dynamics import check_dynamic_tracking
```

## Purpose

Check final forward-dynamics scalar positions against targets.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.dynamic_types.ForwardDynamicsResult` | required | Public input or data field `result`. |
| `targets` | `Mapping[str, float]` | required | Public input or data field `targets`. |
| `tolerance` | `Union[Mapping[str, float], float]` | `0.001` | Public input or data field `tolerance`. |

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
