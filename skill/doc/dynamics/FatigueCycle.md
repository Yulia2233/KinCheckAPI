# `FatigueCycle`

## API Definition

```python
@dataclass(frozen=True)
class FatigueCycle:
    stress_range_pa: float
    mean_stress_pa: float
    count: float
    start_index: int | None
    end_index: int | None
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import FatigueCycle
```

## Purpose

FatigueCycle(*, stress_range_pa: 'float', mean_stress_pa: 'float', count: 'float', start_index: 'int | None' = None, end_index: 'int | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `stress_range_pa` | `float` | required | Public input or data field `stress_range_pa`. |
| `mean_stress_pa` | `float` | required | Public input or data field `mean_stress_pa`. |
| `count` | `float` | required | Public input or data field `count`. |
| `start_index` | `int | None` | `None` | Public input or data field `start_index`. |
| `end_index` | `int | None` | `None` | Public input or data field `end_index`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
