# `count_cycles`

## API Definition

```python
count_cycles(*, stress_pa: Sequence[float], retain_residual: bool = True) -> tuple[kincheckapi.fatigue.FatigueCycle, ...]
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import count_cycles
```

## Purpose

Count cycles with the ASTM four-point rainflow stack.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `stress_pa` | `Sequence[float]` | required | Public input or data field `stress_pa`. |
| `retain_residual` | `bool` | `True` | Public input or data field `retain_residual`. |

## Returns and Failures

Returns `tuple[FatigueCycle, ...]`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
