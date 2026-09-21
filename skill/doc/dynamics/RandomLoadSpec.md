# `RandomLoadSpec`

## API Definition

```python
@dataclass(frozen=True)
class RandomLoadSpec:
    frequency_hz: tuple[float, ...]
    psd: tuple[float, ...]
    unit: str
    seed: int | None
    one_sided: bool
    source: str
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import RandomLoadSpec
```

## Purpose

RandomLoadSpec(*, frequency_hz: 'tuple[float, ...]', psd: 'tuple[float, ...]', unit: 'str', seed: 'int | None' = None, one_sided: 'bool' = True, source: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `frequency_hz` | `tuple[float, ...]` | required | Public input or data field `frequency_hz`. |
| `psd` | `tuple[float, ...]` | required | Public input or data field `psd`. |
| `unit` | `str` | required | Public input or data field `unit`. |
| `seed` | `int | None` | `None` | Public input or data field `seed`. |
| `one_sided` | `bool` | `True` | Public input or data field `one_sided`. |
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
