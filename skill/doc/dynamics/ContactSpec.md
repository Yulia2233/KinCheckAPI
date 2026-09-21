# `ContactSpec`

## API Definition

```python
@dataclass(frozen=True)
class ContactSpec:
    contact_id: str
    normal: tuple[float, float, float]
    friction_coefficient: float
    contact_area_m2: float | None
    allowable_normal_force_n: float | None
    allowable_pressure_pa: float | None
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import ContactSpec
```

## Purpose

A declared planar contact capacity; normal points in the load direction.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `contact_id` | `str` | required | Stable, resolvable `contact_id`. |
| `normal` | `tuple[float, float, float]` | required | Public input or data field `normal`. |
| `friction_coefficient` | `float` | required | Public input or data field `friction_coefficient`. |
| `contact_area_m2` | `float | None` | `None` | Public input or data field `contact_area_m2`. |
| `allowable_normal_force_n` | `float | None` | `None` | Public input or data field `allowable_normal_force_n`. |
| `allowable_pressure_pa` | `float | None` | `None` | Public input or data field `allowable_pressure_pa`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
