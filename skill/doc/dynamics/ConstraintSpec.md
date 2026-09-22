# `ConstraintSpec`

## API Definition

```python
@dataclass(frozen=True)
class ConstraintSpec:
    constraint_id: str
    coefficients: Mapping[str, float]
    target: float
    velocity_target: float
    acceleration_target: float
    tolerance: float
    source: str
    relation: str
    receiver_ids: tuple[str, ...]
    source_map: Mapping[str, Any]
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ConstraintSpec
```

## Purpose

One linearized scalar constraint Jq=target for a declared state basis.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `constraint_id` | `str` | required | Stable, resolvable constraint ID. |
| `coefficients` | `Mapping[str, float]` | required | Public input or data field `coefficients`. |
| `target` | `float` | `0.0` | Public input or data field `target`. |
| `velocity_target` | `float` | `0.0` | Public input or data field `velocity_target`. |
| `acceleration_target` | `float` | `0.0` | Public input or data field `acceleration_target`. |
| `tolerance` | `float` | `1e-08` | Public input or data field `tolerance`. |
| `source` | `str` | `'declared'` | Public input or data field `source`. |
| `relation` | `str` | `'linear'` | Public input or data field `relation`. |
| `receiver_ids` | `tuple[str, ...]` | `()` | Explicitly specified `receiver_ids` collection. |
| `source_map` | `Mapping[str, Any]` | default_factory | Public input or data field `source_map`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
