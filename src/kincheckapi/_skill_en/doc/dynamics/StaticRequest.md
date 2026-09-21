# `StaticRequest`

## API Definition

```python
@dataclass(frozen=True)
class StaticRequest:
    gravity: kincheckapi.physics_types.GravityField
    supports: tuple[kincheckapi.physics_types.SupportSpec, ...]
    joint_positions: Mapping[str, float]
    joint_modes: Mapping[str, str]
    loads: tuple[kincheckapi.physics_types.WrenchLoad, ...]
    request_individual_support_reactions: bool
    force_tolerance_n: float
    moment_tolerance_nm: float
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import StaticRequest
```

## Purpose

StaticRequest(*, gravity: 'GravityField', supports: 'tuple[SupportSpec, ...]', joint_positions: 'Mapping[str, float]', joint_modes: 'Mapping[str, str]', loads: 'tuple[WrenchLoad, ...]' = (), request_individual_support_reactions: 'bool' = False, force_tolerance_n: 'float' = 0.01, moment_tolerance_nm: 'float' = 0.001)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `gravity` | `kincheckapi.physics_types.GravityField` | required | Public input or data field `gravity`. |
| `supports` | `tuple[kincheckapi.physics_types.SupportSpec, ...]` | required | Public input or data field `supports`. |
| `joint_positions` | `Mapping[str, float]` | required | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `joint_modes` | `Mapping[str, str]` | required | Public input or data field `joint_modes`. |
| `loads` | `tuple[kincheckapi.physics_types.WrenchLoad, ...]` | `()` | Public input or data field `loads`. |
| `request_individual_support_reactions` | `bool` | `False` | Public input or data field `request_individual_support_reactions`. |
| `force_tolerance_n` | `float` | `0.01` | Public input or data field `force_tolerance_n`. |
| `moment_tolerance_nm` | `float` | `0.001` | Public input or data field `moment_tolerance_nm`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
