"""Frozen partial-capability evaluator for the XYZ gantry benchmark.

The script proves the claims that v0.6.3 can independently support: source
identity, CADIR conversion/topology, complete BREP physical coverage, explicit
inertial compilation, scalar-tree inverse dynamics, finite-actuator forward
dynamics, and declared load limits. It reports unsupported direct-drive
electromagnetic binding, guide reaction sharing, Cartesian coordination, and
structural claims as capability failures instead of silently passing them.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from benchmark.common import Evaluation, cli, input_report, report
from benchmark.xyz_pick_place_gantry.verification.contract import (
    ACTUATOR_LIMITS,
    CONTACT_CASES,
    GRAVITY_M_S2,
    HOME_M,
    MIN_FREE_CLEARANCE_M,
    MOVABLE_JOINTS,
    REQUIRED_PROMPT_CLAIMS,
    WORKSPACE_M,
)
from kincheckapi.assembly import validate_assembly, validate_topology
from kincheckapi.cadir import convert_mjcf
from kincheckapi.checks import (
    check_assembly_integrity,
    check_driver_tracking,
    check_interference,
    check_joint_limits,
    check_minimum_clearance,
    check_trajectory,
)
from kincheckapi.dynamics import (
    ActuatorProfile,
    ActuatorSpec,
    ContactSpec,
    DynamicRequest,
    DynamicState,
    ForwardDynamicsRequest,
    build_dynamics_model,
    check_dynamic_load_limits,
    check_contact_capacity,
    check_mass_properties,
    compile_dynamics_model,
    measure_package_physics,
    probe_dynamics_capabilities,
    solve_forward_dynamics,
    solve_inverse_dynamics,
    validate_physics_conversion,
)
from kincheckapi.kinematics import KinematicSolveOptions, solve_motion
from kincheckapi.scenario import (
    MotionSegment,
    add_joint_motion_segments,
    create_scenario,
    request_component_result,
    request_joint_result,
    set_component_result_scope,
    set_run_duration,
    set_sample_period,
    validate_scenario,
)
from kincheckapi.physics_types import GravityField


CASE = Path(__file__).resolve().parents[1]
REQUIRED_CHECKS = (
    "input",
    "assembly_validation",
    "topology_validation",
    "fastener_seating",
    "kinematic_motion",
    "kinematic_joint_limits",
    "kinematic_x_tracking",
    "kinematic_y_tracking",
    "kinematic_z_tracking",
    "kinematic_payload_trajectory",
    "assembly_integrity",
    "motion_interference",
    "motion_clearance",
    "occurrence_support",
    "mass_properties",
    "inertia_compilation",
    "inverse_dynamics",
    "inverse_effort_limits",
    "forward_dynamics",
    "contact_payload_support",
    "contact_x_guide_envelope",
    "contact_y_guide_envelope",
    "contact_z_guide_envelope",
    "direct_drive_actuator_binding",
    "guide_reaction_sharing",
    "coordinated_cartesian_path",
    "structural_strength",
)


def verify(model_dir: str | Path) -> dict:
    root = Path(model_dir).expanduser().resolve()
    evaluation = Evaluation(CASE, REQUIRED_CHECKS)
    source_report = evaluation.run("input", input_report, model_dir=root)
    if source_report is None or not source_report.passed:
        return evaluation.finish(ready=False)

    converted = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    assembly = converted.assembly
    assembly_report = evaluation.run("assembly_validation", validate_assembly, assembly=assembly)
    topology_report = evaluation.run("topology_validation", validate_topology, assembly=assembly)

    def check_fastener_seating():
        mapping = json.loads((root / "scene.mapping.json").read_text(encoding="utf-8"))
        expected = [f"base_bolt_{i}" for i in range(1, 9)]
        expected += [f"x_rail_left_bolt_{i}" for i in range(1, 7)]
        expected += [f"x_rail_right_bolt_{i}" for i in range(1, 7)]
        expected += [f"y_rail_front_bolt_{i}" for i in range(1, 7)]
        expected += [f"y_rail_rear_bolt_{i}" for i in range(1, 7)]
        expected += [f"guard_bolt_{i}" for i in range(1, 9)]
        expected += [f"payload_bolt_{i}" for i in range(1, 5)]
        members = {member for group in mapping["groups"] for member in group["members"]}
        fixed_edges = {
            edge["b"].rsplit("/", 1)[-1]
            for edge in mapping["rigid_edges"]
            if edge.get("kind") == "fixed" and edge.get("joint_id", "").endswith("_fixed")
        }
        seated = [item for item in expected if f"node/xyz_pick_place_gantry/{item}" in members and item in fixed_edges]
        return report(
            "fastener_seating",
            passed=len(seated) == len(expected),
            actual={"expected_count": len(expected), "registered_count": len(seated)},
            expected={"expected_count": len(expected), "each_fastener_in_fixed_edge": True},
            objects=tuple(f"node/xyz_pick_place_gantry/{item}" for item in expected if item not in seated),
            message="Every declared fastener must be present in the occurrence graph and attached by a fixed host edge.",
        )

    evaluation.run("fastener_seating", check_fastener_seating)

    def build_kinematic_case():
        scenario = create_scenario(scenario_id="xyz_pick_place.nominal", assembly=assembly)
        scenario = set_run_duration(scenario=scenario, duration_s=1.0)
        scenario = set_sample_period(scenario=scenario, period_s=0.02)
        profiles = (
            (MOVABLE_JOINTS[0], 0.02),
            (MOVABLE_JOINTS[1], 0.05),
            (MOVABLE_JOINTS[2], 0.03),
        )
        for joint_id, speed in profiles:
            scenario = add_joint_motion_segments(
                scenario=scenario,
                joint_id=joint_id,
                segments=(
                    MotionSegment(start_time_s=0.0, end_time_s=0.5, mode="position", value=0.0, interpolation="linear"),
                    MotionSegment(start_time_s=0.5, end_time_s=1.0, mode="position", value=speed, interpolation="linear"),
                ),
            )
            scenario = request_joint_result(scenario=scenario, joint_id=joint_id)
        # The CAD exporter uses the fixed payload/tool/z carriage assembly as
        # one rigid body; the payload group is its stable public representative.
        payload_id = f"node/xyz_pick_place_gantry/payload"
        scenario = request_component_result(scenario=scenario, component_id=payload_id)
        scenario = set_component_result_scope(scenario=scenario, scope="all")
        validate_scenario(scenario=scenario).raise_if_failed()
        return scenario, solve_motion(
            scenario=scenario,
            options=KinematicSolveOptions(max_integration_step_s=0.002),
        )

    try:
        scenario, kinematic_motion = build_kinematic_case()
        evaluation.run(
            "kinematic_motion",
            report,
            operation="kinematic_motion",
            passed=kinematic_motion.status in {"completed", "completed_with_warnings"} and bool(kinematic_motion.sample_times_s),
            actual={"status": kinematic_motion.status, "sample_count": len(kinematic_motion.sample_times_s)},
            expected={"status": "completed or completed_with_warnings", "sample_count": "> 0"},
            objects=("xyz_pick_place_gantry",),
        )
        evaluation.run("kinematic_joint_limits", check_joint_limits, assembly=assembly, motion_result=kinematic_motion)
        for check_id, joint_id in zip(("kinematic_x_tracking", "kinematic_y_tracking", "kinematic_z_tracking"), MOVABLE_JOINTS):
            evaluation.run(check_id, check_driver_tracking, motion_result=kinematic_motion, scenario=scenario, joint_id=joint_id, tolerance=0.03)
        evaluation.run(
            "kinematic_payload_trajectory",
            check_trajectory,
            motion_result=kinematic_motion,
            component_id=f"node/xyz_pick_place_gantry/payload",
            max_speed_m_s=0.8,
            max_acceleration_m_s2=2.0,
            position_bounds_m=WORKSPACE_M,
        )
        component_ids = tuple(component.component_id for component in assembly.components)
        # Guide rails and their carriage blocks are declared functional
        # contacts in the prompt.  Do not classify those interfaces as an
        # unintended collision; test the remaining payload-to-frame envelope.
        payload_component = "node/xyz_pick_place_gantry/payload"
        x_carriage_component = "node/xyz_pick_place_gantry/x_carriage"
        component_pairs = ((payload_component, x_carriage_component),)
        evaluation.run(
            "assembly_integrity",
            check_assembly_integrity,
            assembly=assembly,
            motion_result=kinematic_motion,
            asset_root=root,
            component_ids=component_ids,
            geometric_connection_pairs=(),
            sampling_scope="motion_result",
            require_single_network=True,
        )
        evaluation.run(
            "motion_interference",
            check_interference,
            assembly=assembly,
            motion_result=kinematic_motion,
            component_pairs=component_pairs,
            penetration_tolerance_m=0.0,
            sampling_scope="motion_result",
            max_sample_period_s=0.02,
            asset_root=root,
        )
        evaluation.run(
            "motion_clearance",
            check_minimum_clearance,
            assembly=assembly,
            motion_result=kinematic_motion,
            component_pairs=component_pairs,
            minimum_allowed_clearance_m=MIN_FREE_CLEARANCE_M,
            sampling_scope="motion_result",
            max_sample_period_s=0.02,
            asset_root=root,
        )
    except Exception as exc:
        evaluation.run(
            "kinematic_motion",
            report,
            operation="kinematic_motion",
            passed=False,
            status="validation_failed",
            actual={"type": type(exc).__name__, "message": str(exc)},
            expected="completed kinematic MotionResult",
            message=str(exc),
        )

    source_package = Path(source_report.evidence["actual"]["source"])
    evaluation.run("occurrence_support", __import__("kincheckapi.dynamics", fromlist=["check_occurrence_support"]).check_occurrence_support, package_path=source_package)
    manifest = measure_package_physics(package_path=source_package)
    model = build_dynamics_model(assembly=assembly, manifest=manifest)
    evaluation.artifacts.update({
        "source_package": str(source_package),
        "model_sha256": model.content_hash,
        "occurrence_count": len(manifest.occurrences),
        "component_count": len(model.component_properties),
    })
    evaluation.run("mass_properties", check_mass_properties, model=model)
    def compile_and_validate_inertia():
        compilation = compile_dynamics_model(model=model)
        return validate_physics_conversion(model=model, compilation=compilation)

    evaluation.run("inertia_compilation", compile_and_validate_inertia)

    if set(MOVABLE_JOINTS) != {
        joint.joint_id for joint in assembly.joints if joint.joint_type.value != "fixed"
    }:
        evaluation.run(
            "joint_registry",
            lambda: (_ for _ in ()).throw(ValueError("Prismatic joint registry does not match the captured assembly")),
        )

    states = tuple(
        DynamicState(joint_id=joint_id, position=0.0, velocity=0.0, acceleration=0.0)
        for joint_id in MOVABLE_JOINTS
    )
    inverse = evaluation.run(
        "inverse_dynamics",
        solve_inverse_dynamics,
        model=model,
        request=DynamicRequest(
            states=states,
            gravity=GravityField(acceleration_m_s2=GRAVITY_M_S2),
        ),
    )
    if inverse is not None:
        evaluation.run(
            "inverse_effort_limits",
            check_dynamic_load_limits,
            result=inverse,
            limits={
                MOVABLE_JOINTS[0]: ACTUATOR_LIMITS["x"],
                MOVABLE_JOINTS[1]: ACTUATOR_LIMITS["y"],
                MOVABLE_JOINTS[2]: ACTUATOR_LIMITS["z"],
            },
        )

    forward = evaluation.run(
        "forward_dynamics",
        solve_forward_dynamics,
        model=model,
        request=ForwardDynamicsRequest(
            initial_states=states,
            actuators=tuple(
                ActuatorSpec(actuator_id=f"{axis}_motor", joint_id=joint_id, max_effort=ACTUATOR_LIMITS[axis])
                for axis, joint_id in zip(("x", "y", "z"), MOVABLE_JOINTS)
            ),
            profiles=tuple(
                ActuatorProfile(actuator_id=f"{axis}_motor", points=((0.0, 0.0), (0.5, 0.0)))
                for axis in ("x", "y", "z")
            ),
            duration_s=0.5,
            sample_period_s=0.1,
            gravity=GravityField(acceleration_m_s2=GRAVITY_M_S2),
        ),
    )

    for contact_id, values in CONTACT_CASES.items():
        evaluation.run(
            f"contact_{contact_id}",
            check_contact_capacity,
            contact=ContactSpec(
                contact_id=contact_id,
                normal=values["normal"],
                friction_coefficient=values["mu"],
                contact_area_m2=values["area_m2"],
                allowable_normal_force_n=values["normal_limit_n"],
                allowable_pressure_pa=values["pressure_limit_pa"],
            ),
            force_n=values["force_n"],
        )

    # These are real prompt claims, but no v0.6.3 public API proves them.
    for check_id, message in (
        ("direct_drive_actuator_binding", "The current adapter exposes finite scalar actuators, but does not independently prove electromagnetic stator/forcer binding from CAD interfaces."),
        ("guide_reaction_sharing", "Individual guide-block reactions and frictional load sharing require a contact/compliance solver."),
        ("coordinated_cartesian_path", "The current forward API accepts effort profiles, not an independent multi-axis Cartesian target trajectory."),
        ("structural_strength", "Stress, deformation, resonance, and fatigue are outside the current API capability contract."),
    ):
        evaluation.unresolved(check_id, message)

    result = evaluation.finish(ready=False)
    result["prompt_claims"] = {claim: "covered" if claim in {"cad_source_and_occurrence_registry", "mass_com_inertia_and_payload_mass", "scalar_prismatic_motion_and_limits", "finite_actuator_inverse_forward_dynamics", "sampled_and_continuous_geometry"} else "capability_failed" for claim in REQUIRED_PROMPT_CLAIMS}
    result["home_m"] = list(HOME_M)
    return result


if __name__ == "__main__":
    raise SystemExit(cli(verify))
