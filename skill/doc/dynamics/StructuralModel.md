# `StructuralModel`

## API Definition

```python
@dataclass(frozen=True)
class StructuralModel:
    model_id: str
    stiffness_matrix: tuple[tuple[float, ...], ...]
    mass_matrix: tuple[tuple[float, ...], ...] | None
    dof_ids: tuple[str, ...]
    fixed_dofs: tuple[int, ...]
    material: kincheckapi.structural.ElasticMaterial | None
    length_m: float | None
    area_m2: float | None
    second_moment_m4: float | None
    polar_moment_m4: float | None
    mesh_hash: str | None
    mesh_quality: Mapping[str, float]
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import StructuralModel
```

## Purpose

StructuralModel(*, model_id: 'str', stiffness_matrix: 'tuple[tuple[float, ...], ...]', mass_matrix: 'tuple[tuple[float, ...], ...] | None' = None, dof_ids: 'tuple[str, ...]' = (), fixed_dofs: 'tuple[int, ...]' = (), material: 'ElasticMaterial | None' = None, length_m: 'float | None' = None, area_m2: 'float | None' = None, second_moment_m4: 'float | None' = None, polar_moment_m4: 'float | None' = None, mesh_hash: 'str | None' = None, mesh_quality: 'Mapping[str, float]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model_id` | `str` | required | Stable, resolvable `model_id`. |
| `stiffness_matrix` | `tuple[tuple[float, ...], ...]` | required | Public input or data field `stiffness_matrix`. |
| `mass_matrix` | `tuple[tuple[float, ...], ...] | None` | `None` | Public input or data field `mass_matrix`. |
| `dof_ids` | `tuple[str, ...]` | `()` | Explicitly specified `dof_ids` collection. |
| `fixed_dofs` | `tuple[int, ...]` | `()` | Public input or data field `fixed_dofs`. |
| `material` | `kincheckapi.structural.ElasticMaterial | None` | `None` | Public input or data field `material`. |
| `length_m` | `float | None` | `None` | `length_m` in metres; finite. |
| `area_m2` | `float | None` | `None` | Public input or data field `area_m2`. |
| `second_moment_m4` | `float | None` | `None` | Public input or data field `second_moment_m4`. |
| `polar_moment_m4` | `float | None` | `None` | Public input or data field `polar_moment_m4`. |
| `mesh_hash` | `str | None` | `None` | Public input or data field `mesh_hash`. |
| `mesh_quality` | `Mapping[str, float]` | default_factory | Public input or data field `mesh_quality`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
