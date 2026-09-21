# `Payload`

## API Definition

```python
@dataclass(frozen=True)
class Payload:
    payload_id: str
    component_id: str
    cad_occurrence_id: str | None
    properties: kincheckapi.physics_types.RigidBodyProperties | None
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import Payload
```

## Purpose

Payload(*, payload_id: 'str', component_id: 'str', cad_occurrence_id: 'str | None' = None, properties: 'RigidBodyProperties | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `payload_id` | `str` | required | Stable, resolvable `payload_id`. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `cad_occurrence_id` | `str | None` | `None` | Stable, resolvable `cad_occurrence_id`. |
| `properties` | `kincheckapi.physics_types.RigidBodyProperties | None` | `None` | Public input or data field `properties`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
