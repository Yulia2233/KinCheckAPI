"""Complete acceptance program for the detailed slider-crank example.

The verifier consumes only the exported KinCheckAPI model directory.  It checks
structural validity, the driven motion, closure residuals, joint limits,
trajectory bounds, mesh interference, minimum clearances, and whole-assembly
connectivity/guide containment over every recorded sample.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kincheckapi.assembly import validate_assembly, validate_topology
from kincheckapi.cadir import convert_mjcf
from kincheckapi.checks import (
    ContainmentRelation,
    check_assembly_integrity,
    check_constraint_residuals,
    check_driver_tracking,
    check_interference,
    check_joint_limits,
    check_minimum_clearance,
    check_trajectory,
)
from kincheckapi.errors import KinCheckError
from kincheckapi.kinematics import KinematicSolveOptions, solve_motion
from kincheckapi.scenario import (
    MotionSegment,
    add_joint_motion_segments,
    create_scenario,
    request_component_result,
    request_joint_result,
    set_capture_integration_steps,
    set_component_result_scope,
    set_initial_joint_position,
    set_run_duration,
    set_sample_period,
    validate_scenario,
)

CRANK = "joint/slider_crank/joint.crank"
SLIDER = "joint/slider_crank/joint.slider"
ROOT = "node/slider_crank"
CRANK_COMPONENT = "node/slider_crank/crank"
ROD_COMPONENT = "node/slider_crank/connecting_rod"
SLIDER_COMPONENT = "node/slider_crank/slider"
COMPONENT_PAIRS = (
    (ROOT, CRANK_COMPONENT),
    (ROOT, ROD_COMPONENT),
    (ROOT, SLIDER_COMPONENT),
    (CRANK_COMPONENT, ROD_COMPONENT),
    (CRANK_COMPONENT, SLIDER_COMPONENT),
    (ROD_COMPONENT, SLIDER_COMPONENT),
)


def solve(model_dir: str | Path):
    """Build the fixed nominal scenario and return assembly, scenario, motion."""
    root = Path(model_dir).expanduser().resolve()
    converted = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    assembly = converted.assembly
    validate_assembly(assembly=assembly).raise_if_failed()
    validate_topology(assembly=assembly).raise_if_failed()

    scenario = create_scenario(scenario_id="slider_crank.nominal", assembly=assembly)
    scenario = set_initial_joint_position(scenario=scenario, joint_id=CRANK, position_rad_or_m=0.0)
    scenario = set_run_duration(scenario=scenario, duration_s=2.0)
    scenario = set_sample_period(scenario=scenario, period_s=0.01)
    scenario = add_joint_motion_segments(
        scenario=scenario,
        joint_id=CRANK,
        segments=(
            MotionSegment(start_time_s=0.0, end_time_s=0.2, mode="speed", value=0.0, interpolation="linear"),
            MotionSegment(start_time_s=0.2, end_time_s=1.8, mode="speed", value=2.0, interpolation="linear"),
            MotionSegment(start_time_s=1.8, end_time_s=2.0, mode="speed", value=0.0, interpolation="linear"),
        ),
    )
    scenario = request_joint_result(scenario=scenario, joint_id=CRANK)
    scenario = request_joint_result(scenario=scenario, joint_id=SLIDER)
    scenario = request_component_result(scenario=scenario, component_id=SLIDER_COMPONENT)
    scenario = set_component_result_scope(scenario=scenario, scope="all")
    scenario = set_capture_integration_steps(
        scenario=scenario, enabled=True, component_ids=(SLIDER_COMPONENT,)
    )
    validate_scenario(scenario=scenario).raise_if_failed()
    motion = solve_motion(
        scenario=scenario,
        options=KinematicSolveOptions(max_integration_step_s=0.001),
    )
    return assembly, scenario, motion


def verify(model_dir: str | Path):
    """Return a structured acceptance result; no failed check is hidden."""
    root = Path(model_dir).expanduser().resolve()
    assembly, scenario, motion = solve(root)
    checks = (
        check_constraint_residuals(
            motion_result=motion,
            position_tolerance_m=1e-5,
            orientation_tolerance_rad=1e-5,
        ),
        check_driver_tracking(
            motion_result=motion, scenario=scenario, joint_id=CRANK, tolerance=0.05
        ),
        check_joint_limits(assembly=assembly, motion_result=motion),
        check_trajectory(
            motion_result=motion,
            component_id=SLIDER_COMPONENT,
            max_speed_m_s=10.0,
            max_acceleration_m_s2=100.0,
            min_path_length_m=0.01,
        ),
        check_interference(
            assembly=assembly,
            motion_result=motion,
            component_pairs=COMPONENT_PAIRS,
            penetration_tolerance_m=0.0,
            sampling_scope="motion_result",
            max_sample_period_s=0.01,
            asset_root=root,
        ),
        check_minimum_clearance(
            assembly=assembly,
            motion_result=motion,
            component_pairs=COMPONENT_PAIRS,
            minimum_allowed_clearance_m=0.0005,
            sampling_scope="motion_result",
            max_sample_period_s=0.01,
            asset_root=root,
        ),
    )
    integrity = check_assembly_integrity(
        assembly=assembly,
        motion_result=motion,
        asset_root=root,
        component_ids=(ROOT, CRANK_COMPONENT, ROD_COMPONENT, SLIDER_COMPONENT),
        geometric_connection_pairs=(),
        containment_relations=(ContainmentRelation(
            relation_id="slider-guide-envelope",
            contained_component_id=SLIDER_COMPONENT,
            container_component_id=ROOT,
            axis=(1.0, 0.0, 0.0),
            min_position_m=0.10,
            max_position_m=0.20,
            allowed_escape_tolerance_m=0.001,
        ),),
        sampling_scope="motion_result",
        require_single_network=True,
    )
    passed = motion.status in {"completed", "completed_with_warnings"} and all(
        item.passed for item in checks
    ) and integrity.passed
    return {
        "passed": passed,
        "motion": motion.to_dict(),
        "checks": [item.to_dict() for item in checks],
        "assembly_integrity": integrity.to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.model_dir)
    except Exception as error:
        payload = error.to_dict() if isinstance(error, KinCheckError) else {
            "status": "failed",
            "error_type": type(error).__name__,
            "message": str(error),
        }
        print(json.dumps(payload, sort_keys=True))
        return 1
    print(json.dumps({
        "passed": result["passed"],
        "motion_status": result["motion"]["status"],
        "sample_count": len(result["motion"]["sample_times_s"]),
        "integration_sample_count": len(result["motion"].get("integration_samples", ())),
        "checks": [
            {"check_id": item.get("check_id", item.get("operation", "unknown")), "passed": item["passed"]}
            for item in result["checks"]
        ],
        "assembly_integrity": {
            "passed": result["assembly_integrity"]["passed"],
            "status": result["assembly_integrity"]["status"],
            "checked_sample_count": result["assembly_integrity"]["checked_sample_count"],
        },
    }, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
