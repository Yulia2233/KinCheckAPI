# Geometric Safety

Check mesh interference, minimum clearance, and motion envelopes at discrete motion samples.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`ClearanceReport`](ClearanceReport.md) | Type | ClearanceReport(*, operation: "Literal['interference', 'minimum_clearance', 'motion_envelope']", passed: 'bool', status: "Literal['passed', 'failed', 'capability_failed', 'partial']", events: 'tuple[InterferenceEvent, ...]' = (), measurements: 'tuple[MinimumClearance, ...]' = (), envelopes: 'tuple[MotionEnvelope, ...]' = (), checked_component_pair_count: 'int' = 0, checked_sample_count: 'int' = 0, first_failure_time_s: 'float | None' = None, maximum_penetration_depth_m: 'float' = 0.0, backend_id: 'str | None' = 'python-fcl', backend_version: 'str | None' = None, sampling_scope: 'SamplingScope' = 'motion_result', sampling_period_s: 'float' = 0.0, issues: 'tuple[SimIssue, ...]' = (), metadata: 'Mapping[str, Any]' = <factory>) |
| [`EnvelopeSample`](EnvelopeSample.md) | Type | World-space bounds of one real mesh at one recorded time. |
| [`MinimumClearance`](MinimumClearance.md) | Type | MinimumClearance(*, component_a_id: 'str', component_b_id: 'str', minimum_clearance_m: 'float', time_s: 'float', closest_point_a_m: 'tuple[float, float, float] | None' = None, closest_point_b_m: 'tuple[float, float, float] | None' = None, backend_id: 'str' = 'python-fcl', sampling_scope: 'SamplingScope' = 'motion_result') |
| [`MotionEnvelope`](MotionEnvelope.md) | Type | MotionEnvelope(*, component_id: 'str', world_min_position_m: 'tuple[float, float, float]', world_max_position_m: 'tuple[float, float, float]', sample_times_s: 'tuple[float, ...]', mesh_vertex_count: 'int', mesh_path: 'str', mesh_sha256: 'str | None' = None, mesh_triangle_count: 'int | None' = None, sample_bounds: 'tuple[EnvelopeSample, ...]' = (), backend_id: 'str' = 'python-fcl', sampling_scope: 'SamplingScope' = 'motion_result') |
| [`SamplingScope`](SamplingScope.md) | Type alias | Define the public type contract used by `SamplingScope`. |
| [`check_envelope_interference`](check_envelope_interference.md) | Function | Compare world-axis-aligned bounds from two motion-envelope reports; this does not perform triangle-mesh interference or confirm penetration. |
| [`check_interference`](check_interference.md) | Function | Check specified component pairs for mesh penetration at discrete motion samples. |
| [`create_motion_envelope`](create_motion_envelope.md) | Function | Create a discrete motion envelope for specified components for later spatial interference analysis. |
| [`measure_minimum_clearance`](measure_minimum_clearance.md) | Function | Measure minimum signed clearance for specified component pairs at discrete motion samples. |
| [`write_motion_envelope`](write_motion_envelope.md) | Function | Write a public object deterministically: `write_motion_envelope`. |

## Module Rules

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Results come from triangle meshes and discrete time samples; they are not continuous-time collision proofs.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.
