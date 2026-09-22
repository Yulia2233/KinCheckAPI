# `ElasticMaterial`

## API Definition

```python
@dataclass(frozen=True)
class ElasticMaterial:
    material_id: str
    youngs_modulus_pa: float
    poisson_ratio: float
    density_kg_m3: float
    source: str
    yield_strength_pa: float | None
    ultimate_strength_pa: float | None
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import ElasticMaterial
```

## Purpose

ElasticMaterial(*, material_id: 'str', youngs_modulus_pa: 'float', poisson_ratio: 'float', density_kg_m3: 'float', source: 'str', yield_strength_pa: 'float | None' = None, ultimate_strength_pa: 'float | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `material_id` | `str` | required | Stable, resolvable `material_id`. |
| `youngs_modulus_pa` | `float` | required | Public input or data field `youngs_modulus_pa`. |
| `poisson_ratio` | `float` | required | Public input or data field `poisson_ratio`. |
| `density_kg_m3` | `float` | required | Public input or data field `density_kg_m3`. |
| `source` | `str` | required | Public input or data field `source`. |
| `yield_strength_pa` | `float | None` | `None` | Public input or data field `yield_strength_pa`. |
| `ultimate_strength_pa` | `float | None` | `None` | Public input or data field `ultimate_strength_pa`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
