# Scenarios and Drivers

Define initial state, drivers, run duration, sampling, and result recording scope.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`ComponentResultScope`](ComponentResultScope.md) | Enum | Which component world-pose trajectories a scenario records. |
| [`ComponentResultRequest`](ComponentResultRequest.md) | Type | ComponentResultRequest(*, component_id: 'str', connector_id: 'str | None' = None) |
| [`Interpolation`](Interpolation.md) | Enum | str(object='') -> str str(bytes_or_buffer[, encoding[, errors]]) -> str Create a new string object from the given object. If encoding or errors is specified, then the object must expose a data buffer that will be decoded using the given encoding and error handler. Otherwise, returns the result of object.__str__() (if defined) or repr(object). encoding defaults to sys.getdefaultencoding(). errors defaults to 'strict'. |
| [`JointLock`](JointLock.md) | Type | JointLock(*, joint_id: 'str', position_rad_or_m: 'float | None' = None) |
| [`JointResultRequest`](JointResultRequest.md) | Type | JointResultRequest(*, joint_id: 'str') |
| [`JointValue`](JointValue.md) | Type | JointValue(*, joint_id: 'str', value: 'float') |
| [`MotionProfile`](MotionProfile.md) | Type | MotionProfile(*, points: 'tuple[ProfilePoint, ...]', interpolation: 'Interpolation | str' = <Interpolation.LINEAR: 'linear'>) |
| [`PositionDriver`](PositionDriver.md) | Type | PositionDriver(*, joint_id: 'str', profile: 'MotionProfile') |
| [`Profile`](Profile.md) | Type alias | MotionProfile(*, points: 'tuple[ProfilePoint, ...]', interpolation: 'Interpolation | str' = <Interpolation.LINEAR: 'linear'>) |
| [`ProfilePoint`](ProfilePoint.md) | Type | ProfilePoint(*, time_s: 'float', value: 'float') |
| [`Scenario`](Scenario.md) | Type | A reusable kinematic condition bound to exactly one assembly definition. |
| [`SpeedDriver`](SpeedDriver.md) | Type | SpeedDriver(*, joint_id: 'str', profile: 'MotionProfile', active_interval_s: 'tuple[float, float] | None' = None) |
| [`add_joint_position_driver`](add_joint_position_driver.md) | Function | Add data and return the updated immutable object: `add_joint_position_driver`. |
| [`add_joint_speed_driver`](add_joint_speed_driver.md) | Function | Add data and return the updated immutable object: `add_joint_speed_driver`. |
| [`add_joint_speed_profile`](add_joint_speed_profile.md) | Function | Add data and return the updated immutable object: `add_joint_speed_profile`. |
| [`create_scenario`](create_scenario.md) | Function | Create an empty scenario referencing an immutable assembly model. |
| [`disable_constraint`](disable_constraint.md) | Function | Disable a constraint by stable ID in a Scenario; use only for explicit diagnostic or comparison conditions. |
| [`lock_joint`](lock_joint.md) | Function | Lock a specified joint in a Scenario, optionally at a position; this changes the verification condition. |
| [`read_scenario`](read_scenario.md) | Function | Read and reconstruct a public object: `read_scenario`. |
| [`request_component_result`](request_component_result.md) | Function | Request recording of an object in the result: `request_component_result`. |
| [`request_joint_result`](request_joint_result.md) | Function | Request recording of an object in the result: `request_joint_result`. |
| [`scenario_from_dict`](scenario_from_dict.md) | Function | Reconstruct a Scenario bound to a specified AssemblyModel from a parsed mapping; strict validation remains separate. |
| [`scenario_to_dict`](scenario_to_dict.md) | Function | Convert Scenario into a deterministic JSON-compatible dictionary. |
| [`set_initial_joint_position`](set_initial_joint_position.md) | Function | Set a field and return the updated immutable object: `set_initial_joint_position`. |
| [`set_initial_joint_velocity`](set_initial_joint_velocity.md) | Function | Set a field and return the updated immutable object: `set_initial_joint_velocity`. |
| [`set_component_result_scope`](set_component_result_scope.md) | Function | Select component trajectory recording scope. `all` always records all components; `requested` records requested objects when the list is non-empty and preserves the historical all-components behavior when empty. |
| [`set_capture_integration_steps`](set_capture_integration_steps.md) | Function | Opt into retaining every internal physics backend integration-step pose. The default is off to keep long MotionResults compact. Clearance checks using ``sampling_scope='solver_steps'`` require this explicit capture. |
| [`set_joint_home_position`](set_joint_home_position.md) | Function | Set a field and return the updated immutable object: `set_joint_home_position`. |
| [`set_run_duration`](set_run_duration.md) | Function | Set a field and return the updated immutable object: `set_run_duration`. |
| [`set_sample_period`](set_sample_period.md) | Function | Set a field and return the updated immutable object: `set_sample_period`. |
| [`validate_scenario`](validate_scenario.md) | Function | Aggregate time, reference, limit, and driver conflict errors. |
| [`write_scenario`](write_scenario.md) | Function | Write a public object deterministically: `write_scenario`. |

## Module Rules

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.
