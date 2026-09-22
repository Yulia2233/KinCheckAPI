# `ContactInterface`

## API Definition

```python
@dataclass(frozen=True)
class ContactInterface:
    contact_id: str
    normal: tuple[float, float, float]
    gap_m: float
    body_a: str
    body_b: str
    contact_point_m: tuple[float, float, float]
    coordinate_frame: str
    dof_coefficients: Mapping[str, float]
    tangential_coefficients: tuple[Mapping[str, float], ...]
    friction_coefficient: float
    normal_stiffness_n_m: float | None
    normal_damping_n_s_m: float
    restitution: float | None
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ContactInterface
```

## Purpose

ContactInterface(*, contact_id: 'str', normal: 'tuple[float, float, float]', gap_m: 'float', body_a: 'str' = '', body_b: 'str' = '', contact_point_m: 'tuple[float, float, float]' = (0.0, 0.0, 0.0), coordinate_frame: 'str' = 'world', dof_coefficients: 'Mapping[str, float]' = <factory>, tangential_coefficients: 'tuple[Mapping[str, float], ...]' = (), friction_coefficient: 'float' = 0.0, normal_stiffness_n_m: 'float | None' = None, normal_damping_n_s_m: 'float' = 0.0, restitution: 'float | None' = None, source: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `contact_id` | `str` | required | Stable, resolvable `contact_id`. |
| `normal` | `tuple[float, float, float]` | required | Public input or data field `normal`. |
| `gap_m` | `float` | required | `gap_m` in metres; finite. |
| `body_a` | `str` | `''` | Public input or data field `body_a`. |
| `body_b` | `str` | `''` | Public input or data field `body_b`. |
| `contact_point_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `contact_point_m` in metres; finite. |
| `coordinate_frame` | `str` | `'world'` | Public input or data field `coordinate_frame`. |
| `dof_coefficients` | `Mapping[str, float]` | default_factory | Public input or data field `dof_coefficients`. |
| `tangential_coefficients` | `tuple[Mapping[str, float], ...]` | `()` | Public input or data field `tangential_coefficients`. |
| `friction_coefficient` | `float` | `0.0` | Public input or data field `friction_coefficient`. |
| `normal_stiffness_n_m` | `float | None` | `None` | `normal_stiffness_n_m` in metres; finite. |
| `normal_damping_n_s_m` | `float` | `0.0` | `normal_damping_n_s_m` in metres; finite. |
| `restitution` | `float | None` | `None` | Public input or data field `restitution`. |
| `source` | `str` | `'declared'` | Public input or data field `source`. |

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
