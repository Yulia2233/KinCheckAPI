# `solve_static_structure`

## API Definition

```python
solve_static_structure(*, model: kincheckapi.structural.StructuralModel, loads: Sequence[kincheckapi.structural.StructuralLoad] = (), load_vector: Optional[Sequence[float]] = None, fixed_dofs: Optional[Sequence[int]] = None, maps: Sequence[kincheckapi.structural.LoadTransferMap] = (), roi: Sequence[str] = ()) -> kincheckapi.structural.StructuralResult
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import solve_static_structure
```

## Purpose

Solve K u = f for a declared linear model with explicit supports.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.structural.StructuralModel` | required | Public input or data field `model`. |
| `loads` | `Sequence[kincheckapi.structural.StructuralLoad]` | `()` | Public input or data field `loads`. |
| `load_vector` | `Optional[Sequence[float]]` | `None` | Public input or data field `load_vector`. |
| `fixed_dofs` | `Optional[Sequence[int]]` | `None` | Public input or data field `fixed_dofs`. |
| `maps` | `Sequence[kincheckapi.structural.LoadTransferMap]` | `()` | Public input or data field `maps`. |
| `roi` | `Sequence[str]` | `()` | Public input or data field `roi`. |

## Returns and Failures

Returns `StructuralResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
