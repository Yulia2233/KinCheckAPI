# `solve_buckling_screening`

## API Definition

```python
solve_buckling_screening(*, model: kincheckapi.structural.StructuralModel, compressive_load_n: float | None = None, mode_count: int = 3, effective_length_factor: float = 1.0, geometric_stiffness_matrix: Optional[Sequence[Sequence[float]]] = None) -> kincheckapi.structural.BucklingResult
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import solve_buckling_screening
```

## Purpose

Return generalized eigenvalue screening or Euler load for a beam model.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.structural.StructuralModel` | required | Public input or data field `model`. |
| `compressive_load_n` | `float | None` | `None` | Public input or data field `compressive_load_n`. |
| `mode_count` | `int` | `3` | Public input or data field `mode_count`. |
| `effective_length_factor` | `float` | `1.0` | Public input or data field `effective_length_factor`. |
| `geometric_stiffness_matrix` | `Optional[Sequence[Sequence[float]]]` | `None` | Public input or data field `geometric_stiffness_matrix`. |

## Returns and Failures

Returns `BucklingResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
