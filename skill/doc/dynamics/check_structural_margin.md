# `check_structural_margin`

## API Definition

```python
check_structural_margin(*, result: kincheckapi.structural.StructuralResult, allowable_stress_pa: float | None = None, material: kincheckapi.structural.ElasticMaterial | None = None, allowable_displacement_m: float | None = None) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import check_structural_margin
```

## Purpose

Execute a structured check: `check_structural_margin`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.structural.StructuralResult` | required | Public input or data field `result`. |
| `allowable_stress_pa` | `float | None` | `None` | Public input or data field `allowable_stress_pa`. |
| `material` | `kincheckapi.structural.ElasticMaterial | None` | `None` | Public input or data field `material`. |
| `allowable_displacement_m` | `float | None` | `None` | `allowable_displacement_m` in metres; finite. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
