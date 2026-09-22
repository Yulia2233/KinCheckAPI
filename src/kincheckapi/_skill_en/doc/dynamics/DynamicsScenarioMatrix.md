# `DynamicsScenarioMatrix`

## API Definition

```python
@dataclass(frozen=True)
class DynamicsScenarioMatrix:
    matrix_id: str
    cases: tuple[kincheckapi.dynamics_v07.DynamicsScenarioCase, ...]
    requested_case_ids: tuple[str, ...] | None
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import DynamicsScenarioMatrix
```

## Purpose

A finite, auditable set of cases; an empty matrix is never acceptance-passed.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `matrix_id` | `str` | required | Stable, resolvable `matrix_id`. |
| `cases` | `tuple[kincheckapi.dynamics_v07.DynamicsScenarioCase, ...]` | required | Public input or data field `cases`. |
| `requested_case_ids` | `tuple[str, ...] | None` | `None` | Explicitly specified `requested_case_ids` collection. |
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
