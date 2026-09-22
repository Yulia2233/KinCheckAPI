# `estimate_psd`

## API Definition

```python
estimate_psd(*, times_s: Sequence[float], values: Sequence[float], unit: str, segment_length: int | None = None, overlap: float = 0.5) -> kincheckapi.vibration.PSDResult
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import estimate_psd
```

## Purpose

Execute the public operation `estimate_psd`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `times_s` | `Sequence[float]` | required | `times_s` in seconds; finite. |
| `values` | `Sequence[float]` | required | Public input or data field `values`. |
| `unit` | `str` | required | Public input or data field `unit`. |
| `segment_length` | `int | None` | `None` | Public input or data field `segment_length`. |
| `overlap` | `float` | `0.5` | Public input or data field `overlap`. |

## Returns and Failures

Returns `PSDResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
