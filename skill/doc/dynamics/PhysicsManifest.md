# `PhysicsManifest`

## API Definition

```python
@dataclass(frozen=True)
class PhysicsManifest:
    definitions: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    occurrences: tuple[kincheckapi.physics_types.PhysicsOccurrence, ...]
    source_path: str
    source_sha256: str
    producer: Mapping[str, str]
    schema_version: str
    algorithm: str
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import PhysicsManifest
```

## Purpose

PhysicsManifest(*, definitions: 'Mapping[str, RigidBodyProperties]', occurrences: 'tuple[PhysicsOccurrence, ...]', source_path: 'str', source_sha256: 'str', producer: 'Mapping[str, str]', schema_version: 'str' = 'kincheck.physics/1.0', algorithm: 'str' = 'occt-volume-com-tensor-si/1')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `definitions` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | required | Public input or data field `definitions`. |
| `occurrences` | `tuple[kincheckapi.physics_types.PhysicsOccurrence, ...]` | required | Public input or data field `occurrences`. |
| `source_path` | `str` | required | Public input or data field `source_path`. |
| `source_sha256` | `str` | required | Public input or data field `source_sha256`. |
| `producer` | `Mapping[str, str]` | required | Public input or data field `producer`. |
| `schema_version` | `str` | `'kincheck.physics/1.0'` | Public input or data field `schema_version`. |
| `algorithm` | `str` | `'occt-volume-com-tensor-si/1'` | Public input or data field `algorithm`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
