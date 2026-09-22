# `DynamicsScenarioCase`

## API Definition

```python
@dataclass(frozen=True)
class DynamicsScenarioCase:
    case_id: str
    scenario: kincheckapi.dynamics_v07.RigidDynamicsScenario
    reaction_request: kincheckapi.dynamics_v07.ReactionRequest | None
    tags: tuple[str, ...]
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import DynamicsScenarioCase
```

## Purpose

One independently identifiable rigid-body operating case.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `case_id` | `str` | required | Stable, resolvable `case_id`. |
| `scenario` | `kincheckapi.dynamics_v07.RigidDynamicsScenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `reaction_request` | `kincheckapi.dynamics_v07.ReactionRequest | None` | `None` | Public input or data field `reaction_request`. |
| `tags` | `tuple[str, ...]` | `()` | Public input or data field `tags`. |

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
