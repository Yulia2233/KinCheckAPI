# `set_initial_joint_position`

## API Definition

```python
set_initial_joint_position(*, scenario: Scenario, joint_id: str, position_rad_or_m: float) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import set_initial_joint_position
```

## Purpose

Set a field and return the updated immutable object: `set_initial_joint_position`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `position_rad_or_m` | `float` | required | `position_rad_or_m` in metres; finite. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
