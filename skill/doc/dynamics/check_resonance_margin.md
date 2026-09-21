# `check_resonance_margin`

## API Definition

```python
check_resonance_margin(*, natural_frequencies_hz: Sequence[float], excitation_frequencies_hz: Sequence[float], minimum_margin_hz: float, damping_ratio: float = 0.0) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import check_resonance_margin
```

## Purpose

Execute a structured check: `check_resonance_margin`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `natural_frequencies_hz` | `Sequence[float]` | required | Public input or data field `natural_frequencies_hz`. |
| `excitation_frequencies_hz` | `Sequence[float]` | required | Public input or data field `excitation_frequencies_hz`. |
| `minimum_margin_hz` | `float` | required | Public input or data field `minimum_margin_hz`. |
| `damping_ratio` | `float` | `0.0` | Public input or data field `damping_ratio`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
