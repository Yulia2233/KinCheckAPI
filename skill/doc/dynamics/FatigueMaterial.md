# `FatigueMaterial`

## API Definition

```python
@dataclass(frozen=True)
class FatigueMaterial:
    material_id: str
    sn_points: tuple[tuple[float, float], ...]
    ultimate_strength_pa: float | None
    fatigue_limit_pa: float | None
    source: str
    confidence: float
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import FatigueMaterial
```

## Purpose

FatigueMaterial(*, material_id: 'str', sn_points: 'tuple[tuple[float, float], ...]', ultimate_strength_pa: 'float | None' = None, fatigue_limit_pa: 'float | None' = None, source: 'str' = 'declared', confidence: 'float' = 0.5)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `material_id` | `str` | required | Stable, resolvable `material_id`. |
| `sn_points` | `tuple[tuple[float, float], ...]` | required | Public input or data field `sn_points`. |
| `ultimate_strength_pa` | `float | None` | `None` | Public input or data field `ultimate_strength_pa`. |
| `fatigue_limit_pa` | `float | None` | `None` | Public input or data field `fatigue_limit_pa`. |
| `source` | `str` | `'declared'` | Public input or data field `source`. |
| `confidence` | `float` | `0.5` | Public input or data field `confidence`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
