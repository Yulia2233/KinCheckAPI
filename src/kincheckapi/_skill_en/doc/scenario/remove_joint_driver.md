# `remove_joint_driver`

## API Definition

```python
remove_joint_driver(*, scenario: Scenario, joint_id: str) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import remove_joint_driver
```

## Purpose

Execute the public operation `remove_joint_driver`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
