# `RigidBodyProperties`

## API Definition

```python
@dataclass(frozen=True)
class RigidBodyProperties:
    mass_kg: float
    com_m: tuple[float, float, float]
    inertia_com_kg_m2: tuple[tuple[float, float, float], ...]
    frame_id: str
    source_kind: str
    source_ids: tuple[str, ...]
    provenance: Mapping[str, Any]
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import RigidBodyProperties
```

## Purpose

RigidBodyProperties(*, mass_kg: 'float', com_m: 'tuple[float, float, float]', inertia_com_kg_m2: 'tuple[tuple[float, float, float], ...]', frame_id: 'str', source_kind: 'str', source_ids: 'tuple[str, ...]', provenance: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `mass_kg` | `float` | required | Public input or data field `mass_kg`. |
| `com_m` | `tuple[float, float, float]` | required | `com_m` in metres; finite. |
| `inertia_com_kg_m2` | `tuple[tuple[float, float, float], ...]` | required | Public input or data field `inertia_com_kg_m2`. |
| `frame_id` | `str` | required | Stable, resolvable `frame_id`. |
| `source_kind` | `str` | required | Public input or data field `source_kind`. |
| `source_ids` | `tuple[str, ...]` | required | Explicitly specified `source_ids` collection. |
| `provenance` | `Mapping[str, Any]` | default_factory | Public input or data field `provenance`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
