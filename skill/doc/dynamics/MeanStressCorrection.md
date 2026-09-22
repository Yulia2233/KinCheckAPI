# `MeanStressCorrection`

## API Definition

```python
@dataclass(frozen=True)
class MeanStressCorrection:
    method: str
    ultimate_strength_pa: float | None
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import MeanStressCorrection
```

## Purpose

MeanStressCorrection(*, method: 'str' = 'goodman', ultimate_strength_pa: 'float | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `method` | `str` | `'goodman'` | Public input or data field `method`. |
| `ultimate_strength_pa` | `float | None` | `None` | Public input or data field `ultimate_strength_pa`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
