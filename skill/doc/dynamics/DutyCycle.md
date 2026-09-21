# `DutyCycle`

## API Definition

```python
@dataclass(frozen=True)
class DutyCycle:
    duty_id: str
    stages: tuple[tuple[str, int], ...]
    source: str
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import DutyCycle
```

## Purpose

DutyCycle(*, duty_id: 'str', stages: 'tuple[tuple[str, int], ...]', source: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `duty_id` | `str` | required | Stable, resolvable `duty_id`. |
| `stages` | `tuple[tuple[str, int], ...]` | required | Public input or data field `stages`. |
| `source` | `str` | `'declared'` | Public input or data field `source`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
