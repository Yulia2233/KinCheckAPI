# `solve_modes`

## API Definition

```python
solve_modes(*, model: kincheckapi.structural.StructuralModel, request: kincheckapi.vibration.ModalRequest = ModalRequest(mode_count=6, fixed_dofs=(), frequency_min_hz=0.0, frequency_max_hz=None)) -> kincheckapi.vibration.ModalResult
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import solve_modes
```

## Purpose

Solve the specified kinematic problem: `solve_modes`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.structural.StructuralModel` | required | Public input or data field `model`. |
| `request` | `kincheckapi.vibration.ModalRequest` | `ModalRequest(mode_count=6, fixed_dofs=(), frequency_min_hz=0.0, frequency_max_hz=None)` | Public input or data field `request`. |

## Returns and Failures

Returns `ModalResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
