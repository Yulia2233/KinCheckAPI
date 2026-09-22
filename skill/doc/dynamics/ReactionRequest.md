# `ReactionRequest`

## API Definition

```python
@dataclass(frozen=True)
class ReactionRequest:
    object_ids: tuple[str, ...]
    mode: str
    reference_frame: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ReactionRequest
```

## Purpose

ReactionRequest(*, object_ids: 'tuple[str, ...]', mode: 'str' = 'identifiable', reference_frame: 'str' = 'world')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `object_ids` | `tuple[str, ...]` | required | Explicitly specified `object_ids` collection. |
| `mode` | `str` | `'identifiable'` | Public input or data field `mode`. |
| `reference_frame` | `str` | `'world'` | Public input or data field `reference_frame`. |

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
