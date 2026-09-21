# `ScenarioMatrix`

## API Definition

```python
@dataclass(frozen=True)
class ScenarioMatrix:
    cases: Mapping[str, Mapping[str, Any]]
    search_strategy: str
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import ScenarioMatrix
```

## Purpose

ScenarioMatrix(*, cases: 'Mapping[str, Mapping[str, Any]]', search_strategy: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `cases` | `Mapping[str, Mapping[str, Any]]` | required | Public input or data field `cases`. |
| `search_strategy` | `str` | `'declared'` | Public input or data field `search_strategy`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
