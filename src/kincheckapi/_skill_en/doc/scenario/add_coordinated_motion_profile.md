# `add_coordinated_motion_profile`

## API Definition

```python
add_coordinated_motion_profile(*, scenario: Scenario, profile: kincheckapi.motion_contracts.CoordinatedMotionProfile) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import add_coordinated_motion_profile
```

## Purpose

Convert one shared-time scalar target into one position driver per axis.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `profile` | `kincheckapi.motion_contracts.CoordinatedMotionProfile` | required | Public input or data field `profile`. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
