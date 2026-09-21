# `evaluate_operating_envelope`

## API Definition

```python
evaluate_operating_envelope(*, cases: Mapping[str, tuple[kincheckapi.fatigue.StressHistory, kincheckapi.fatigue.FatigueMaterial]], correction: kincheckapi.fatigue.MeanStressCorrection = MeanStressCorrection(method='none', ultimate_strength_pa=None), allowable_damage: float = 1.0, scenario_matrix: kincheckapi.fatigue.ScenarioMatrix | None = None) -> kincheckapi.fatigue.OperatingEnvelopeReport
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import evaluate_operating_envelope
```

## Purpose

Execute the public operation `evaluate_operating_envelope`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `cases` | `Mapping[str, tuple[kincheckapi.fatigue.StressHistory, kincheckapi.fatigue.FatigueMaterial]]` | required | Public input or data field `cases`. |
| `correction` | `kincheckapi.fatigue.MeanStressCorrection` | `MeanStressCorrection(method='none', ultimate_strength_pa=None)` | Public input or data field `correction`. |
| `allowable_damage` | `float` | `1.0` | Public input or data field `allowable_damage`. |
| `scenario_matrix` | `kincheckapi.fatigue.ScenarioMatrix | None` | `None` | Public input or data field `scenario_matrix`. |

## Returns and Failures

Returns `OperatingEnvelopeReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
