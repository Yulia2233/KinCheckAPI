# `record_dynamics_history`

## API Definition

```python
record_dynamics_history(*, result: kincheckapi.dynamics_v07.MultibodyResult | kincheckapi.dynamics_v07.ContactDynamicsResult, history_id: str = 'dynamics-history') -> kincheckapi.dynamics_v07.DynamicsLoadHistory
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import record_dynamics_history
```

## Purpose

Convert a rigid-body result into a portable load/event history.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.dynamics_v07.MultibodyResult | kincheckapi.dynamics_v07.ContactDynamicsResult` | required | Public input or data field `result`. |
| `history_id` | `str` | `'dynamics-history'` | Stable, resolvable `history_id`. |

## Returns and Failures

Returns `DynamicsLoadHistory`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
