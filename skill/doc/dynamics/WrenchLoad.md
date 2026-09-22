# `WrenchLoad`

## API Definition

```python
@dataclass(frozen=True)
class WrenchLoad:
    load_id: str
    component_id: str
    force_n: tuple[float, float, float]
    moment_nm: tuple[float, float, float]
    point_m: tuple[float, float, float]
    frame_id: str
    applied_by: str
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import WrenchLoad
```

## Purpose

WrenchLoad(*, load_id: 'str', component_id: 'str', force_n: 'tuple[float, float, float]', moment_nm: 'tuple[float, float, float]', point_m: 'tuple[float, float, float]', frame_id: 'str', applied_by: 'str')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `load_id` | `str` | required | Stable, resolvable `load_id`. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `force_n` | `tuple[float, float, float]` | required | Public input or data field `force_n`. |
| `moment_nm` | `tuple[float, float, float]` | required | Public input or data field `moment_nm`. |
| `point_m` | `tuple[float, float, float]` | required | `point_m` in metres; finite. |
| `frame_id` | `str` | required | Stable, resolvable `frame_id`. |
| `applied_by` | `str` | required | Public input or data field `applied_by`. |

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
