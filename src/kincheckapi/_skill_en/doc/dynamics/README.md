# Dynamics Namespace

Real BREP mass properties, typed loads/supports, scalar tree statics and compiled inertia validation.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`ContactRegion`](ContactRegion.md) | Type | Allowed local region in occurrence_a's definition frame, in SI metres. Both named interfaces must resolve to recorded topology. Every closest-point witness must lie inside the region; interpenetrating solids always fail. An ideal clearance fit is a geometric relation, not proof of load sharing. |
| [`check_static_geometry`](check_static_geometry.md) | Function | Check every leaf pair using exact BREP, including fixed-group internals. Broad-phase boxes only prove separation; nearby pairs use BREP distances and solid intersections. No triangle approximation is used for acceptance. |
| [`check_occurrence_support`](check_occurrence_support.md) | Function | Check the actual CAD joint/fastener graph, including every hardware leaf. Hierarchy placement alone is never a mounting relation. This topological gate complements, and cannot replace, geometric mounting/clearance checks. |
| [`read_mjcf_mass_properties`](read_mjcf_mass_properties.md) | Function | Compatibility import of explicit MJCF inertials, labeled mjcf_explicit. Density-only meshes, shell assumptions and unspecified triangulation error have no strict acceptance path in v0.6.0. World mass must be supplied explicitly because MuJoCo worldbody does not retain physical ground mass. |
| [`measure_interface_centers`](measure_interface_centers.md) | Function | Resolve named CAD faces and return their measured definition-frame centres. Used for load attachment evidence, never to infer a missing interface by name or appearance. Coordinates are SI and topology IDs remain in the response. |
| [`DynamicsModel`](DynamicsModel.md) | Type | DynamicsModel(*, assembly: 'AssemblyModel', component_properties: 'Mapping[str, RigidBodyProperties]', body_properties: 'Mapping[str, RigidBodyProperties]', occurrence_components: 'Mapping[str, str]', manifest: 'PhysicsManifest | None' = None, payloads: 'tuple[Payload, ...]' = (), base_component_properties: 'Mapping[str, RigidBodyProperties]' = <factory>) |
| [`GravityField`](GravityField.md) | Type | GravityField(*, acceleration_m_s2: 'tuple[float, float, float]') |
| [`Payload`](Payload.md) | Type | Payload(*, payload_id: 'str', component_id: 'str', cad_occurrence_id: 'str | None' = None, properties: 'RigidBodyProperties | None' = None) |
| [`PhysicsError`](PhysicsError.md) | Type | Invalid, unavailable, or conflicting physics input; never a placeholder. |
| [`PhysicsManifest`](PhysicsManifest.md) | Type | PhysicsManifest(*, definitions: 'Mapping[str, RigidBodyProperties]', occurrences: 'tuple[PhysicsOccurrence, ...]', source_path: 'str', source_sha256: 'str', producer: 'Mapping[str, str]', schema_version: 'str' = 'kincheck.physics/1.0', algorithm: 'str' = 'occt-volume-com-tensor-si/1') |
| [`PhysicsMaterial`](PhysicsMaterial.md) | Type | PhysicsMaterial(*, material_id: 'str', density: 'float', density_unit: 'str', source: 'str', data_quality: 'str' = 'illustrative') |
| [`PhysicsOccurrence`](PhysicsOccurrence.md) | Type | PhysicsOccurrence(*, occurrence_id: 'str', definition_id: 'str', revision: 'str', content_hash: 'str', pose_world: 'Pose', properties: 'RigidBodyProperties', interfaces: 'Mapping[str, Any]' = <factory>) |
| [`PhysicsReport`](PhysicsReport.md) | Type | PhysicsReport(*, operation: 'str', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None) |
| [`RigidBodyProperties`](RigidBodyProperties.md) | Type | RigidBodyProperties(*, mass_kg: 'float', com_m: 'tuple[float, float, float]', inertia_com_kg_m2: 'tuple[tuple[float, float, float], ...]', frame_id: 'str', source_kind: 'str', source_ids: 'tuple[str, ...]', provenance: 'Mapping[str, Any]' = <factory>) |
| [`StaticRequest`](StaticRequest.md) | Type | StaticRequest(*, gravity: 'GravityField', supports: 'tuple[SupportSpec, ...]', joint_positions: 'Mapping[str, float]', joint_modes: 'Mapping[str, str]', loads: 'tuple[WrenchLoad, ...]' = (), request_individual_support_reactions: 'bool' = False, force_tolerance_n: 'float' = 0.01, moment_tolerance_nm: 'float' = 0.001) |
| [`StaticResult`](StaticResult.md) | Type | StaticResult(*, operation: 'str' = 'solve_static_equilibrium', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, request: 'StaticRequest | None' = None, generalized_holding: 'Mapping[str, float]' = <factory>, generalized_units: 'Mapping[str, str]' = <factory>, support_wrench: 'Mapping[str, Any]' = <factory>, joint_reactions: 'Mapping[str, Any]' = <factory>, body_residuals: 'Mapping[str, Any]' = <factory>, component_poses: 'Mapping[str, Pose]' = <factory>, load_wrenches: 'tuple[Mapping[str, Any], ...]' = ()) |
| [`SupportSpec`](SupportSpec.md) | Type | SupportSpec(*, support_id: 'str', component_id: 'str', occurrence_id: 'str', interface_name: 'str', kind: 'str' = 'fixed', frame_id: 'str' = 'world', point_m: 'tuple[float, float, float]' = (0.0, 0.0, 0.0), normal: 'tuple[float, float, float]' = (0.0, 0.0, 1.0), evidence_source: 'str | None' = None) |
| [`WrenchLoad`](WrenchLoad.md) | Type | WrenchLoad(*, load_id: 'str', component_id: 'str', force_n: 'tuple[float, float, float]', moment_nm: 'tuple[float, float, float]', point_m: 'tuple[float, float, float]', frame_id: 'str', applied_by: 'str') |
| [`aggregate_mass_properties`](aggregate_mass_properties.md) | Function | Sum every supplied physical instance using the parallel-axis theorem. |
| [`build_dynamics_model`](build_dynamics_model.md) | Function | Bind complete CAD occurrence coverage OR explicit component-frame measurements. |
| [`check_mass_properties`](check_mass_properties.md) | Function | Recompute occurrence transport and aggregation to detect frame/source drift. |
| [`measure_mass_properties`](measure_mass_properties.md) | Function | Integrate one validated closed BREP solid in mm with uniform explicit density. OCCT MatrixOfInertia is already about the volume centroid and has units mm^5. CAD is optional until this entry point is called. No mesh/default mass fallback. |
| [`transform_mass_properties`](transform_mass_properties.md) | Function | Rigid transport; COM inertia rotates but translation adds no parallel-axis term. |
| [`measure_package_physics`](measure_package_physics.md) | Function | Validate .scadpkg, integrate definitions and expand every leaf occurrence. sdk_python explicitly opts into an isolated legacy SDK reader. It never tries another interpreter after failure; actual SDK and encoding enter provenance. Supported tested readers: 2.1.3b3 canonical ticks; 2.0.4b3 legacy millimeters. |
| [`DynamicsCompilation`](DynamicsCompilation.md) | Type | Public inertial evidence, without an exposed mutable simulator handle. |
| [`compile_dynamics_model`](compile_dynamics_model.md) | Function | Compile the actual assembly with explicit m/c/I for every rigid group. |
| [`validate_physics_conversion`](validate_physics_conversion.md) | Function | Audit definition→occurrence→rigid-group→compiled-body conservation. |
| [`check_static_load_limits`](check_static_load_limits.md) | Function | Compare scalar holding demands to positive N/N*m ratings; no stress claim. |
| [`check_support`](check_support.md) | Function | Check fixed support paths and CAD interface identity; no frictional stability claim. |
| [`check_wrench_balance`](check_wrench_balance.md) | Function | Accept only complete per-body force AND moment evidence. |
| [`probe_dynamics_capabilities`](probe_dynamics_capabilities.md) | Function | Probe the requested operation/topology/data/backend combination. |
| [`solve_static_equilibrium`](solve_static_equilibrium.md) | Function | Balance a given tree pose. Holding effort acts on B relative to A. Wrenches are world-expressed, force on the named receiver, moment about the reported reference point. Only locked/hold scalar DOFs can supply effort. |

## Module Rules

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.
