# `add_joint_speed_driver`

## API Definition

```python
add_joint_speed_driver(*, scenario: Scenario, joint_id: str, speed_rad_s_or_m_s: float, start_time_s: float, end_time_s: float) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import add_joint_speed_driver
```

## Purpose

Add data and return the updated immutable object: `add_joint_speed_driver`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `speed_rad_s_or_m_s` | `float` | required | `speed_rad_s_or_m_s` in m/s; finite. |
| `start_time_s` | `float` | required | Start of the time window in seconds. |
| `end_time_s` | `float` | required | End of the time window in seconds. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
