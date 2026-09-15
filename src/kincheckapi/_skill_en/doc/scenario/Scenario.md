# `Scenario`

## API Definition

```python
@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    assembly: AssemblyModel
    assembly_id: str
    initial_joint_positions: tuple[JointValue, ...]
    initial_joint_velocities: tuple[JointValue, ...]
    joint_home_positions: tuple[JointValue, ...]
    locked_joints: tuple[JointLock, ...]
    disabled_constraint_ids: tuple[str, ...]
    position_drivers: tuple[PositionDriver, ...]
    speed_drivers: tuple[SpeedDriver, ...]
    duration_s: float | None
    sample_period_s: float | None
    joint_result_requests: tuple[JointResultRequest, ...]
    component_result_requests: tuple[ComponentResultRequest, ...]
    component_result_scope: ComponentResultScope | str
    capture_integration_steps: bool
    integration_component_ids: tuple[str, ...] | None
    initial_state_source: str
    profile_boundary: ProfileBoundary | str
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import Scenario
```

## Purpose

A reusable kinematic condition bound to exactly one assembly definition.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario_id` | `str` | required | Stable, resolvable `scenario_id`. |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `assembly_id` | `str` | `''` | Stable, resolvable `assembly_id`. |
| `initial_joint_positions` | `tuple[JointValue, ...]` | `()` | Public input or data field `initial_joint_positions`. |
| `initial_joint_velocities` | `tuple[JointValue, ...]` | `()` | Public input or data field `initial_joint_velocities`. |
| `joint_home_positions` | `tuple[JointValue, ...]` | `()` | Public input or data field `joint_home_positions`. |
| `locked_joints` | `tuple[JointLock, ...]` | `()` | Public input or data field `locked_joints`. |
| `disabled_constraint_ids` | `tuple[str, ...]` | `()` | Explicitly specified `disabled_constraint_ids` collection. |
| `position_drivers` | `tuple[PositionDriver, ...]` | `()` | Public input or data field `position_drivers`. |
| `speed_drivers` | `tuple[SpeedDriver, ...]` | `()` | Public input or data field `speed_drivers`. |
| `duration_s` | `float | None` | `None` | Total run duration in seconds; finite and positive. |
| `sample_period_s` | `float | None` | `None` | `sample_period_s` in seconds; finite. |
| `joint_result_requests` | `tuple[JointResultRequest, ...]` | `()` | Public input or data field `joint_result_requests`. |
| `component_result_requests` | `tuple[ComponentResultRequest, ...]` | `()` | Public input or data field `component_result_requests`. |
| `component_result_scope` | `ComponentResultScope | str` | `<ComponentResultScope.REQUESTED: 'requested'>` | Public input or data field `component_result_scope`. |
| `capture_integration_steps` | `bool` | `False` | Public input or data field `capture_integration_steps`. |
| `integration_component_ids` | `tuple[str, ...] | None` | `None` | Explicitly specified `integration_component_ids` collection. |
| `initial_state_source` | `str` | `'explicit'` | Public input or data field `initial_state_source`. |
| `profile_boundary` | `ProfileBoundary | str` | `<ProfileBoundary.HOLD: 'hold'>` | Public input or data field `profile_boundary`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
