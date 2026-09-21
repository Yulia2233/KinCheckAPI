# `check_stress`

## API Definition

```python
check_stress(*, result: kincheckapi.structural.StructuralResult, allowable_stress_pa: float | None = None, material: kincheckapi.structural.ElasticMaterial | None = None, criterion: kincheckapi.structural.FailureCriterion = FailureCriterion(name='maximum_normal', allowable_factor=1.0)) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import check_stress
```

## Purpose

Execute a structured check: `check_stress`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.structural.StructuralResult` | required | Public input or data field `result`. |
| `allowable_stress_pa` | `float | None` | `None` | Public input or data field `allowable_stress_pa`. |
| `material` | `kincheckapi.structural.ElasticMaterial | None` | `None` | Public input or data field `material`. |
| `criterion` | `kincheckapi.structural.FailureCriterion` | `FailureCriterion(name='maximum_normal', allowable_factor=1.0)` | Public input or data field `criterion`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
