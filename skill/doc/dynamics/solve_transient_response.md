# `solve_transient_response`

## API Definition

```python
solve_transient_response(*, model: kincheckapi.structural.StructuralModel, times_s: Sequence[float], force_history: Sequence[Sequence[float]], initial_displacement: Optional[Sequence[float]] = None, initial_velocity: Optional[Sequence[float]] = None, damping: kincheckapi.vibration.DampingSpec = DampingSpec(modal_ratios=(), rayleigh_alpha_s=None, rayleigh_beta_s=None, source='declared')) -> kincheckapi.vibration.TransientResult
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import solve_transient_response
```

## Purpose

Solve the specified kinematic problem: `solve_transient_response`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.structural.StructuralModel` | required | Public input or data field `model`. |
| `times_s` | `Sequence[float]` | required | `times_s` in seconds; finite. |
| `force_history` | `Sequence[Sequence[float]]` | required | Public input or data field `force_history`. |
| `initial_displacement` | `Optional[Sequence[float]]` | `None` | Public input or data field `initial_displacement`. |
| `initial_velocity` | `Optional[Sequence[float]]` | `None` | Public input or data field `initial_velocity`. |
| `damping` | `kincheckapi.vibration.DampingSpec` | `DampingSpec(modal_ratios=(), rayleigh_alpha_s=None, rayleigh_beta_s=None, source='declared')` | Public input or data field `damping`. |

## Returns and Failures

Returns `TransientResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
