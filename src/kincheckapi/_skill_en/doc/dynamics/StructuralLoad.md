# `StructuralLoad`

## API Definition

```python
@dataclass(frozen=True)
class StructuralLoad:
    load_id: str
    values: tuple[float, ...]
    target_dofs: tuple[int, ...]
    source: str
    time_s: float | None
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import StructuralLoad
```

## Purpose

StructuralLoad(*, load_id: 'str', values: 'tuple[float, ...]', target_dofs: 'tuple[int, ...]' = (), source: 'str' = 'explicit', time_s: 'float | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `load_id` | `str` | required | Stable, resolvable `load_id`. |
| `values` | `tuple[float, ...]` | required | Public input or data field `values`. |
| `target_dofs` | `tuple[int, ...]` | `()` | Public input or data field `target_dofs`. |
| `source` | `str` | `'explicit'` | Public input or data field `source`. |
| `time_s` | `float | None` | `None` | Query time in seconds within the result time range. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
