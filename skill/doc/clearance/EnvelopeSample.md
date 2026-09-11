# `EnvelopeSample`

## API Definition

```python
@dataclass(frozen=True)
class EnvelopeSample:
    time_s: float
    world_min_position_m: tuple[float, float, float]
    world_max_position_m: tuple[float, float, float]
```

Source: `src/kincheckapi/clearance_result.py`.

## Import

```python
from kincheckapi.clearance import EnvelopeSample
```

## Purpose

World-space bounds of one real mesh at one recorded time.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `world_min_position_m` | `tuple[float, float, float]` | required | `world_min_position_m` in metres; finite. |
| `world_max_position_m` | `tuple[float, float, float]` | required | `world_max_position_m` in metres; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Results come from triangle meshes and discrete time samples; they are not continuous-time collision proofs.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
