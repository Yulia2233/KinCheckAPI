# `StressHistory`

## API Definition

```python
@dataclass(frozen=True)
class StressHistory:
    history_id: str
    times_s: tuple[float, ...]
    stress_pa: tuple[float, ...]
    unit: str
    region_id: str
    case_id: str
    coordinate_frame: str
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import StressHistory
```

## Purpose

StressHistory(*, history_id: 'str', times_s: 'tuple[float, ...]', stress_pa: 'tuple[float, ...]', unit: 'str' = 'Pa', region_id: 'str' = '', case_id: 'str' = '', coordinate_frame: 'str' = 'material')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `history_id` | `str` | required | Stable, resolvable `history_id`. |
| `times_s` | `tuple[float, ...]` | required | `times_s` in seconds; finite. |
| `stress_pa` | `tuple[float, ...]` | required | Public input or data field `stress_pa`. |
| `unit` | `str` | `'Pa'` | Public input or data field `unit`. |
| `region_id` | `str` | `''` | Stable, resolvable `region_id`. |
| `case_id` | `str` | `''` | Stable, resolvable `case_id`. |
| `coordinate_frame` | `str` | `'material'` | Public input or data field `coordinate_frame`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
