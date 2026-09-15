# `MotionSegment`

## API Definition

```python
@dataclass(frozen=True)
class MotionSegment:
    start_time_s: float
    end_time_s: float
    mode: str
    value: float
    interpolation: Interpolation | str
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import MotionSegment
```

## Purpose

One non-overlapping interval in a joint motion contract.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `start_time_s` | `float` | required | Start of the time window in seconds. |
| `end_time_s` | `float` | required | End of the time window in seconds. |
| `mode` | `str` | required | Public input or data field `mode`. |
| `value` | `float` | required | Public input or data field `value`. |
| `interpolation` | `Interpolation | str` | `<Interpolation.STEP: 'step'>` | Public input or data field `interpolation`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
