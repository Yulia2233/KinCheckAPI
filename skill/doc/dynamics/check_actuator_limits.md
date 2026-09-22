# `check_actuator_limits`

## API Definition

```python
check_actuator_limits(*, result: kincheckapi.dynamics_v07.MultibodyResult, envelope: kincheckapi.dynamics_v07.ActuatorEnvelope) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import check_actuator_limits
```

## Purpose

Execute a structured check: `check_actuator_limits`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.dynamics_v07.MultibodyResult` | required | Public input or data field `result`. |
| `envelope` | `kincheckapi.dynamics_v07.ActuatorEnvelope` | required | Public input or data field `envelope`. |

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
