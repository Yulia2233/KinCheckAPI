# `Profile`

## API Definition

```python
Profile = MotionProfile
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import Profile
```

## Purpose

MotionProfile(*, points: 'tuple[ProfilePoint, ...]', interpolation: 'Interpolation | str' = <Interpolation.LINEAR: 'linear'>)

## Returns and Failures

This is a type contract, not a callable function.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
