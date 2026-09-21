# `FailureCriterion`

## API Definition

```python
@dataclass(frozen=True)
class FailureCriterion:
    name: str
    allowable_factor: float
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import FailureCriterion
```

## Purpose

FailureCriterion(*, name: 'str' = 'von_mises', allowable_factor: 'float' = 1.0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | `'von_mises'` | Public input or data field `name`. |
| `allowable_factor` | `float` | `1.0` | Public input or data field `allowable_factor`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
