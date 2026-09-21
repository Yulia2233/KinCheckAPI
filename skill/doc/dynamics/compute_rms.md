# `compute_rms`

## API Definition

```python
compute_rms(*, frequency_hz: Sequence[float], psd: Sequence[float], mean: float = 0.0) -> float
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import compute_rms
```

## Purpose

Compute a backend-independent kinematic quantity: `compute_rms`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `frequency_hz` | `Sequence[float]` | required | Public input or data field `frequency_hz`. |
| `psd` | `Sequence[float]` | required | Public input or data field `psd`. |
| `mean` | `float` | `0.0` | Public input or data field `mean`. |

## Returns and Failures

Returns `float`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
