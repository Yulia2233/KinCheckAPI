# `DynamicsCompilation`

## API Definition

```python
@dataclass(frozen=True)
class DynamicsCompilation:
    backend: str
    backend_version: str
    model_xml: str
    body_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    source_sha256: str | None
    _compiled: Any
```

Source: `src/kincheckapi/physics_backend.py`.

## Import

```python
from kincheckapi.dynamics import DynamicsCompilation
```

## Purpose

Public inertial evidence, without an exposed mutable simulator handle.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `backend` | `str` | required | Public input or data field `backend`. |
| `backend_version` | `str` | required | Public input or data field `backend_version`. |
| `model_xml` | `str` | required | Public input or data field `model_xml`. |
| `body_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | required | Public input or data field `body_properties`. |
| `source_sha256` | `str | None` | required | Public input or data field `source_sha256`. |
| `_compiled` | `Any` | required | Public input or data field `_compiled`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
