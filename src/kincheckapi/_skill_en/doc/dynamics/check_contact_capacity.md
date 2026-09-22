# `check_contact_capacity`

## API Definition

```python
check_contact_capacity(*, contact: kincheckapi.dynamic_types.ContactSpec, force_n: tuple[float, float, float]) -> kincheckapi.dynamic_types.ContactReport
```

Source: `src/kincheckapi/dynamic_solver.py`.

## Import

```python
from kincheckapi.dynamics import check_contact_capacity
```

## Purpose

Check a declared Coulomb contact capacity. The normal points in the direction of the applied compressive load. This is a capacity check, not a contact-force or impact solver.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `contact` | `kincheckapi.dynamic_types.ContactSpec` | required | Public input or data field `contact`. |
| `force_n` | `tuple[float, float, float]` | required | Public input or data field `force_n`. |

## Returns and Failures

Returns `ContactReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
