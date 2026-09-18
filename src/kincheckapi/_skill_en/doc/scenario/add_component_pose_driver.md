# `add_component_pose_driver`

## API Definition

```python
add_component_pose_driver(*, scenario: Scenario, target: kincheckapi.motion_contracts.PoseTrajectory) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import add_component_pose_driver
```

## Purpose

Explicitly reject Cartesian driving until a 6D backend is available.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `target` | `kincheckapi.motion_contracts.PoseTrajectory` | required | Public input or data field `target`. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
