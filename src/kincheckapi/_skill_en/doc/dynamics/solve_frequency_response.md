# `solve_frequency_response`

## API Definition

```python
solve_frequency_response(*, model: kincheckapi.structural.StructuralModel, frequencies_hz: Sequence[float], force_vector: Sequence[float], damping: kincheckapi.vibration.DampingSpec = DampingSpec(modal_ratios=(), rayleigh_alpha_s=None, rayleigh_beta_s=None, source='declared')) -> kincheckapi.vibration.FrequencyResponseResult
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import solve_frequency_response
```

## Purpose

Solve the specified kinematic problem: `solve_frequency_response`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.structural.StructuralModel` | required | Public input or data field `model`. |
| `frequencies_hz` | `Sequence[float]` | required | Public input or data field `frequencies_hz`. |
| `force_vector` | `Sequence[float]` | required | Public input or data field `force_vector`. |
| `damping` | `kincheckapi.vibration.DampingSpec` | `DampingSpec(modal_ratios=(), rayleigh_alpha_s=None, rayleigh_beta_s=None, source='declared')` | Public input or data field `damping`. |

## Returns and Failures

Returns `FrequencyResponseResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
