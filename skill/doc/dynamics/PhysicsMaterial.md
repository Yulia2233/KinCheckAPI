# `PhysicsMaterial`

## API Definition

```python
@dataclass(frozen=True)
class PhysicsMaterial:
    material_id: str
    density: float
    density_unit: str
    source: str
    data_quality: str
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import PhysicsMaterial
```

## Purpose

PhysicsMaterial(*, material_id: 'str', density: 'float', density_unit: 'str', source: 'str', data_quality: 'str' = 'illustrative')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `material_id` | `str` | required | Stable, resolvable `material_id`. |
| `density` | `float` | required | Public input or data field `density`. |
| `density_unit` | `str` | required | Public input or data field `density_unit`. |
| `source` | `str` | required | Public input or data field `source`. |
| `data_quality` | `str` | `'illustrative'` | Public input or data field `data_quality`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
