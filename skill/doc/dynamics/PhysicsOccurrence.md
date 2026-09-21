# `PhysicsOccurrence`

## API Definition

```python
@dataclass(frozen=True)
class PhysicsOccurrence:
    occurrence_id: str
    definition_id: str
    revision: str
    content_hash: str
    pose_world: Pose
    properties: kincheckapi.physics_types.RigidBodyProperties
    interfaces: Mapping[str, Any]
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import PhysicsOccurrence
```

## Purpose

PhysicsOccurrence(*, occurrence_id: 'str', definition_id: 'str', revision: 'str', content_hash: 'str', pose_world: 'Pose', properties: 'RigidBodyProperties', interfaces: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `occurrence_id` | `str` | required | Stable, resolvable `occurrence_id`. |
| `definition_id` | `str` | required | Stable, resolvable `definition_id`. |
| `revision` | `str` | required | Public input or data field `revision`. |
| `content_hash` | `str` | required | Public input or data field `content_hash`. |
| `pose_world` | `Pose` | required | Public input or data field `pose_world`. |
| `properties` | `kincheckapi.physics_types.RigidBodyProperties` | required | Public input or data field `properties`. |
| `interfaces` | `Mapping[str, Any]` | default_factory | Public input or data field `interfaces`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
