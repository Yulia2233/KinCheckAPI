# Scenarios and Drivers

Define initial state, drivers, run duration, sampling, and result recording scope.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`ComponentResultScope`](ComponentResultScope.md) | Enum | Define the stable enum values accepted by `ComponentResultScope`. |
| [`ComponentResultRequest`](ComponentResultRequest.md) | Type | ComponentResultRequest(*, component_id: 'str', connector_id: 'str | None' = None) |
| [`Interpolation`](Interpolation.md) | Enum | Define the stable enum values accepted by `Interpolation`. |
| [`ProfileBoundary`](ProfileBoundary.md) | Enum | Define the stable enum values accepted by `ProfileBoundary`. |
| [`JointLock`](JointLock.md) | Type | JointLock(*, joint_id: 'str', position_rad_or_m: 'float | None' = None) |
| [`JointResultRequest`](JointResultRequest.md) | Type | JointResultRequest(*, joint_id: 'str') |
| [`JointValue`](JointValue.md) | Type | JointValue(*, joint_id: 'str', value: 'float') |
| [`MotionProfile`](MotionProfile.md) | Type | MotionProfile(*, points: 'tuple[ProfilePoint, ...]', interpolation: 'Interpolation | str' = <Interpolation.LINEAR: 'linear'>) |
| [`MotionSegment`](MotionSegment.md) | Type | One non-overlapping interval in a joint motion contract. |
| [`PositionDriver`](PositionDriver.md) | Type | PositionDriver(*, joint_id: 'str', profile: 'MotionProfile') |
| [`Profile`](Profile.md) | Type alias | MotionProfile(*, points: 'tuple[ProfilePoint, ...]', interpolation: 'Interpolation | str' = <Interpolation.LINEAR: 'linear'>) |
| [`ProfilePoint`](ProfilePoint.md) | Type | ProfilePoint(*, time_s: 'float', value: 'float') |
| [`Scenario`](Scenario.md) | Type | A reusable kinematic condition bound to exactly one assembly definition. |
| [`SpeedDriver`](SpeedDriver.md) | Type | SpeedDriver(*, joint_id: 'str', profile: 'MotionProfile', active_interval_s: 'tuple[float, float] | None' = None) |
| [`add_joint_position_driver`](add_joint_position_driver.md) | Function | Add data and return the updated immutable object: `add_joint_position_driver`. |
| [`add_joint_speed_driver`](add_joint_speed_driver.md) | Function | Add data and return the updated immutable object: `add_joint_speed_driver`. |
| [`add_joint_speed_profile`](add_joint_speed_profile.md) | Function | Add data and return the updated immutable object: `add_joint_speed_profile`. |
| [`add_joint_motion_segments`](add_joint_motion_segments.md) | Function | Add an ordered piecewise position or speed driver for one joint. |
| [`create_scenario`](create_scenario.md) | Function | Create an empty scenario referencing an immutable assembly model. |
| [`disable_constraint`](disable_constraint.md) | Function | Disable a constraint by stable ID in a Scenario; use only for explicit diagnostic or comparison conditions. |
| [`replace_joint_driver`](replace_joint_driver.md) | Function | Execute the public operation `replace_joint_driver`. |
| [`remove_joint_driver`](remove_joint_driver.md) | Function | Execute the public operation `remove_joint_driver`. |
| [`clear_joint_drivers`](clear_joint_drivers.md) | Function | Execute the public operation `clear_joint_drivers`. |
| [`lock_joint`](lock_joint.md) | Function | Lock a specified joint in a Scenario, optionally at a position; this changes the verification condition. |
| [`read_scenario`](read_scenario.md) | Function | Read and reconstruct a public object: `read_scenario`. |
| [`request_component_result`](request_component_result.md) | Function | Request recording of an object in the result: `request_component_result`. |
| [`request_joint_result`](request_joint_result.md) | Function | Request recording of an object in the result: `request_joint_result`. |
| [`scenario_from_dict`](scenario_from_dict.md) | Function | Reconstruct a Scenario bound to a specified AssemblyModel from a parsed mapping; strict validation remains separate. |
| [`scenario_to_dict`](scenario_to_dict.md) | Function | Convert Scenario into a deterministic JSON-compatible dictionary. |
| [`set_initial_joint_position`](set_initial_joint_position.md) | Function | Set a field and return the updated immutable object: `set_initial_joint_position`. |
| [`set_initial_joint_velocity`](set_initial_joint_velocity.md) | Function | Set a field and return the updated immutable object: `set_initial_joint_velocity`. |
| [`set_initial_state_from_home`](set_initial_state_from_home.md) | Function | Use declared home positions as the solver's initial state. |
| [`reset_to_home`](reset_to_home.md) | Function | Execute the public operation `reset_to_home`. |
| [`set_component_result_scope`](set_component_result_scope.md) | Function | Select component trajectory recording scope. `all` always records all components; `requested` records requested objects when the list is non-empty and preserves the historical all-components behavior when empty. |
| [`set_capture_integration_steps`](set_capture_integration_steps.md) | Function | Opt into retaining every internal physics backend integration-step pose. The default is off to keep long MotionResults compact. Clearance checks using ``sampling_scope='solver_steps'`` require this explicit capture. |
| [`set_joint_home_position`](set_joint_home_position.md) | Function | Set a field and return the updated immutable object: `set_joint_home_position`. |
| [`set_run_duration`](set_run_duration.md) | Function | Set a field and return the updated immutable object: `set_run_duration`. |
| [`set_sample_period`](set_sample_period.md) | Function | Set a field and return the updated immutable object: `set_sample_period`. |
| [`set_profile_boundary`](set_profile_boundary.md) | Function | Set a field and return the updated immutable object: `set_profile_boundary`. |
| [`validate_scenario`](validate_scenario.md) | Function | Aggregate time, reference, limit, and driver conflict errors. |
| [`write_scenario`](write_scenario.md) | Function | Write a public object deterministically: `write_scenario`. |

## Module Rules

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.
