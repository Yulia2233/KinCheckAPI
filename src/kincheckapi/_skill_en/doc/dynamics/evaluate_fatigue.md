# `evaluate_fatigue`

## API Definition

```python
evaluate_fatigue(*, history: kincheckapi.fatigue.StressHistory, material: kincheckapi.fatigue.FatigueMaterial, correction: kincheckapi.fatigue.MeanStressCorrection = MeanStressCorrection(method='none', ultimate_strength_pa=None), repeat_count: int = 1, allowable_damage: float = 1.0) -> kincheckapi.fatigue.FatigueReport
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import evaluate_fatigue
```

## Purpose

Execute the public operation `evaluate_fatigue`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `history` | `kincheckapi.fatigue.StressHistory` | required | Public input or data field `history`. |
| `material` | `kincheckapi.fatigue.FatigueMaterial` | required | Public input or data field `material`. |
| `correction` | `kincheckapi.fatigue.MeanStressCorrection` | `MeanStressCorrection(method='none', ultimate_strength_pa=None)` | Public input or data field `correction`. |
| `repeat_count` | `int` | `1` | Public input or data field `repeat_count`. |
| `allowable_damage` | `float` | `1.0` | Public input or data field `allowable_damage`. |

## Returns and Failures

Returns `FatigueReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
