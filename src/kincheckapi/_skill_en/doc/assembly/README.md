# Assembly Model and Topology

Define immutable assembly objects, construct part and component relationships, and validate kinematic topology.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`AssemblyModel`](AssemblyModel.md) | Type | AssemblyModel(assembly_id: 'str', parts: 'tuple[Part, ...]' = (), components: 'tuple[Component, ...]' = (), joints: 'tuple[Joint, ...]' = (), constraints: 'tuple[Constraint, ...]' = (), couplings: 'tuple[Coupling, ...]' = (), closures: 'tuple[Closure, ...]' = (), grounds: 'tuple[Ground, ...]' = (), collision_exclusions: 'tuple[tuple[str, str], ...]' = (), display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`Closure`](Closure.md) | Type | Closure(closure_id: 'str', constraint: 'Constraint', position_tolerance_m: 'float' = 1e-06, orientation_tolerance_rad: 'float' = 1e-06) |
| [`Component`](Component.md) | Type | Component(component_id: 'str', part_id: 'str', initial_pose: 'Pose' = <factory>, connectors: 'tuple[Connector, ...]' = (), display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`Connector`](Connector.md) | Type | Connector(connector_id: 'str', pose: 'Pose' = <factory>, display_name: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`ConnectorRef`](ConnectorRef.md) | Type | ConnectorRef(component_id: 'str', connector_id: 'str') |
| [`Constraint`](Constraint.md) | Type | Constraint(constraint_id: 'str', connector_a: 'ConnectorRef', connector_b: 'ConnectorRef', constraint_type: 'str' = 'coincident', display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`Coupling`](Coupling.md) | Type | Coupling(coupling_id: 'str', coupling_type: 'CouplingType | str', joint_a_id: 'str', joint_b_id: 'str', ratio: 'float', phase_offset: 'float' = 0.0, display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`CouplingType`](CouplingType.md) | Enum | Define the stable enum values accepted by `CouplingType`. |
| [`Ground`](Ground.md) | Type | Ground(component_id: 'str') |
| [`Joint`](Joint.md) | Type | Joint(joint_id: 'str', joint_type: 'JointType | str', connector_a: 'ConnectorRef', connector_b: 'ConnectorRef', limit: 'JointLimit | None' = None, display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`JointLimit`](JointLimit.md) | Type | JointLimit(lower: 'float', upper: 'float') |
| [`JointType`](JointType.md) | Enum | Define the stable enum values accepted by `JointType`. |
| [`KinematicEdge`](KinematicEdge.md) | Type | One directed movable-joint edge in an analyzed kinematic graph. |
| [`KinematicTree`](KinematicTree.md) | Type | Backend-independent analysis of rigid groups and movable joints. |
| [`Limit`](Limit.md) | Type alias | JointLimit(lower: 'float', upper: 'float') |
| [`Part`](Part.md) | Type | Part(part_id: 'str', connectors: 'tuple[Connector, ...]' = (), asset_paths: 'Mapping[str, str]' = <factory>, asset_hashes: 'Mapping[str, str]' = <factory>, display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>) |
| [`Pose`](Pose.md) | Type | Rigid transform expressed in SI units with an xyzw quaternion. |
| [`add_closure_constraint`](add_closure_constraint.md) | Function | Add data and return the updated immutable object: `add_closure_constraint`. |
| [`add_component`](add_component.md) | Function | Add data and return the updated immutable object: `add_component`. |
| [`add_constraint`](add_constraint.md) | Function | Add data and return the updated immutable object: `add_constraint`. |
| [`add_coupling`](add_coupling.md) | Function | Add data and return the updated immutable object: `add_coupling`. |
| [`add_joint`](add_joint.md) | Function | Add data and return the updated immutable object: `add_joint`. |
| [`add_part`](add_part.md) | Function | Add data and return the updated immutable object: `add_part`. |
| [`assembly_from_dict`](assembly_from_dict.md) | Function | Reconstruct AssemblyModel from a parsed mapping; assembly and topology validation are still required. |
| [`assembly_to_dict`](assembly_to_dict.md) | Function | Convert AssemblyModel into a deterministic JSON-compatible dictionary. |
| [`create_assembly`](create_assembly.md) | Function | Create a public object: `create_assembly`. |
| [`build_kinematic_tree`](build_kinematic_tree.md) | Function | Analyze rigid groups, motion-tree edges, closure edges, ground, and disconnected islands; this is topology analysis, not motion solving. |
| [`exclude_collision_pair`](exclude_collision_pair.md) | Function | Add two distinct existing components to the collision exclusion set; this changes later geometric acceptance scope. |
| [`ground_component`](ground_component.md) | Function | Mark an existing component as fixed in the assembly reference frame and return a new assembly. |
| [`read_assembly`](read_assembly.md) | Function | Read and reconstruct a public object: `read_assembly`. |
| [`set_joint_limits`](set_joint_limits.md) | Function | Set a field and return the updated immutable object: `set_joint_limits`. |
| [`validate_assembly`](validate_assembly.md) | Function | Aggregate consistency checks for assembly IDs, references, endpoints, ground, joints, constraints, closures, and couplings. |
| [`validate_topology`](validate_topology.md) | Function | Validate motion-graph boundaries, connectivity, ground, tree edges, and closure edges before solving. |
| [`write_assembly`](write_assembly.md) | Function | Write a public object deterministically: `write_assembly`. |

## Module Rules

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.
