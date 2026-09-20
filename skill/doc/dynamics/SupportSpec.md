# `SupportSpec`

## API Definition

```python
@dataclass(frozen=True)
class SupportSpec:
    support_id: str
    component_id: str
    occurrence_id: str
    interface_name: str
    kind: str
    frame_id: str
    point_m: tuple[float, float, float]
    normal: tuple[float, float, float]
    evidence_source: str | None
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import SupportSpec
```

## Purpose

SupportSpec(*, support_id: 'str', component_id: 'str', occurrence_id: 'str', interface_name: 'str', kind: 'str' = 'fixed', frame_id: 'str' = 'world', point_m: 'tuple[float, float, float]' = (0.0, 0.0, 0.0), normal: 'tuple[float, float, float]' = (0.0, 0.0, 1.0), evidence_source: 'str | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `support_id` | `str` | required | Stable, resolvable `support_id`. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `occurrence_id` | `str` | required | Stable, resolvable `occurrence_id`. |
| `interface_name` | `str` | required | Public input or data field `interface_name`. |
| `kind` | `str` | `'fixed'` | Public input or data field `kind`. |
| `frame_id` | `str` | `'world'` | Stable, resolvable `frame_id`. |
| `point_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `point_m` in metres; finite. |
| `normal` | `tuple[float, float, float]` | `(0.0, 0.0, 1.0)` | Public input or data field `normal`. |
| `evidence_source` | `str | None` | `None` | Public input or data field `evidence_source`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
