# `DutyCycle`

## API Definition

```python
@dataclass(frozen=True)
class DutyCycle:
    duty_id: str
    case_ids: tuple[str, ...]
    repetitions: tuple[int, ...]
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import DutyCycle
```

## Purpose

DutyCycle(*, duty_id: 'str', case_ids: 'tuple[str, ...]', repetitions: 'tuple[int, ...]' = (), source: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `duty_id` | `str` | required | Stable, resolvable `duty_id`. |
| `case_ids` | `tuple[str, ...]` | required | Explicitly specified `case_ids` collection. |
| `repetitions` | `tuple[int, ...]` | `()` | Public input or data field `repetitions`. |
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
