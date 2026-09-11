# `MotionProfile`

## API Definition

```python
@dataclass(frozen=True)
class MotionProfile:
    points: tuple[ProfilePoint, ...]
    interpolation: Interpolation | str
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import MotionProfile
```

## Purpose

MotionProfile(*, points: 'tuple[ProfilePoint, ...]', interpolation: 'Interpolation | str' = <Interpolation.LINEAR: 'linear'>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `points` | `tuple[ProfilePoint, ...]` | required | Public input or data field `points`. |
| `interpolation` | `Interpolation | str` | `<Interpolation.LINEAR: 'linear'>` | Public input or data field `interpolation`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
