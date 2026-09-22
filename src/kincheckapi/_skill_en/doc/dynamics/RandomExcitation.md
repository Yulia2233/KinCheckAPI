# `RandomExcitation`

## API Definition

```python
@dataclass(frozen=True)
class RandomExcitation:
    excitation_id: str
    seed: int
    sample_rate_hz: float
    bandwidth_hz: float
    samples: tuple[float, ...]
    algorithm: str
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import RandomExcitation
```

## Purpose

RandomExcitation(*, excitation_id: 'str', seed: 'int', sample_rate_hz: 'float', bandwidth_hz: 'float', samples: 'tuple[float, ...]', algorithm: 'str' = 'declared-samples', source: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `excitation_id` | `str` | required | Stable, resolvable `excitation_id`. |
| `seed` | `int` | required | Public input or data field `seed`. |
| `sample_rate_hz` | `float` | required | Public input or data field `sample_rate_hz`. |
| `bandwidth_hz` | `float` | required | Public input or data field `bandwidth_hz`. |
| `samples` | `tuple[float, ...]` | required | Public input or data field `samples`. |
| `algorithm` | `str` | `'declared-samples'` | Public input or data field `algorithm`. |
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
