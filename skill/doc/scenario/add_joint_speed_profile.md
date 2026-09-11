# `add_joint_speed_profile`

## API Definition

```python
add_joint_speed_profile(*, scenario: Scenario, joint_id: str, profile: Union[MotionProfile, Mapping[str, Any], Sequence[Any]]) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import add_joint_speed_profile
```

## Purpose

Add data and return the updated immutable object: `add_joint_speed_profile`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `profile` | `Union[MotionProfile, Mapping[str, Any], Sequence[Any]]` | required | Public input or data field `profile`. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
