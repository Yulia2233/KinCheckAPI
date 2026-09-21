# `check_deflection`

## API Definition

```python
check_deflection(*, result: kincheckapi.structural.StructuralResult, allowable_displacement_m: float) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import check_deflection
```

## Purpose

Execute a structured check: `check_deflection`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.structural.StructuralResult` | required | Public input or data field `result`. |
| `allowable_displacement_m` | `float` | required | `allowable_displacement_m` in metres; finite. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
