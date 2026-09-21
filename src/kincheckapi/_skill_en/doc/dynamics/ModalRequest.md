# `ModalRequest`

## API Definition

```python
@dataclass(frozen=True)
class ModalRequest:
    mode_count: int
    fixed_dofs: tuple[int, ...]
    frequency_min_hz: float
    frequency_max_hz: float | None
    participation_vector: tuple[float, ...]
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import ModalRequest
```

## Purpose

ModalRequest(*, mode_count: 'int' = 6, fixed_dofs: 'tuple[int, ...]' = (), frequency_min_hz: 'float' = 0.0, frequency_max_hz: 'float | None' = None, participation_vector: 'tuple[float, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `mode_count` | `int` | `6` | Public input or data field `mode_count`. |
| `fixed_dofs` | `tuple[int, ...]` | `()` | Public input or data field `fixed_dofs`. |
| `frequency_min_hz` | `float` | `0.0` | Public input or data field `frequency_min_hz`. |
| `frequency_max_hz` | `float | None` | `None` | Public input or data field `frequency_max_hz`. |
| `participation_vector` | `tuple[float, ...]` | `()` | Public input or data field `participation_vector`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
