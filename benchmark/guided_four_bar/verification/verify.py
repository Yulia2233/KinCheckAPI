"""Independent KinCheckAPI acceptance program for the guided four-bar actuator."""
from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import combinations
from pathlib import Path

if __package__:
    from .collision_checks import check_fixed_hardware, detector_negative_control
else:
    from collision_checks import check_fixed_hardware, detector_negative_control

from kincheckapi.cadir import convert_mjcf
from kincheckapi.assembly import validate_assembly, validate_topology
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
from kincheckapi.clearance import check_continuous_interference
from kincheckapi.continuous_result import ContinuousInterferenceOptions
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

ROOT = "node/guided_four_bar_actuator"
BASE = f"{ROOT}/base"
CRANK = f"{ROOT}/crank"
COUPLER = f"{ROOT}/coupler"
ROCKER = f"{ROOT}/rocker"
CRANK_JOINT = "joint/guided_four_bar_actuator/crank_to_ground"
COUPLER_JOINT = "joint/guided_four_bar_actuator/coupler_to_crank"
ROCKER_JOINT = "joint/guided_four_bar_actuator/rocker_to_ground"
COMPONENT_PAIRS = tuple(combinations(sorted((ROOT, CRANK, COUPLER, ROCKER)), 2))
# Revolute-connected groups are included. A joint never licenses penetration.



def solve(model_dir: str | Path):
    root = Path(model_dir).expanduser().resolve()
    converted = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    assembly = converted.assembly
    validate_assembly(assembly=assembly).raise_if_failed()
    validate_topology(assembly=assembly).raise_if_failed()

    scenario = create_scenario(scenario_id="guided_four_bar.nominal", assembly=assembly)
    scenario = set_initial_joint_position(
        scenario=scenario, joint_id=CRANK_JOINT, position_rad_or_m=0.0
    )
    scenario = set_run_duration(scenario=scenario, duration_s=2.0)
    scenario = set_sample_period(scenario=scenario, period_s=0.01)
    scenario = add_joint_motion_segments(
        scenario=scenario,
        joint_id=CRANK_JOINT,
        segments=(
            MotionSegment(start_time_s=0.0, end_time_s=0.2, mode="speed", value=0.0, interpolation="linear"),
            MotionSegment(start_time_s=0.2, end_time_s=1.8, mode="speed", value=0.8, interpolation="linear"),
            MotionSegment(start_time_s=1.8, end_time_s=2.0, mode="speed", value=0.0, interpolation="linear"),
        ),
    )
    scenario = request_joint_result(scenario=scenario, joint_id=CRANK_JOINT)
    scenario = request_joint_result(scenario=scenario, joint_id=COUPLER_JOINT)
    scenario = request_joint_result(scenario=scenario, joint_id=ROCKER_JOINT)
    scenario = request_component_result(scenario=scenario, component_id=CRANK)
    scenario = request_component_result(scenario=scenario, component_id=COUPLER)
    scenario = request_component_result(scenario=scenario, component_id=ROCKER)
    scenario = set_component_result_scope(scenario=scenario, scope="all")
    scenario = set_capture_integration_steps(
        scenario=scenario, enabled=True, component_ids=(CRANK, COUPLER, ROCKER)
    )
    validate_scenario(scenario=scenario).raise_if_failed()
    motion = solve_motion(
        scenario=scenario,
        options=KinematicSolveOptions(max_integration_step_s=0.001),
    )
    return assembly, scenario, motion


def _run_check(function, **kwargs):
    started = time.monotonic()
    print(f"[verify] {function.__name__}: started", file=sys.stderr, flush=True)
    result = function(**kwargs)
    print(f"[verify] {function.__name__}: completed in {time.monotonic() - started:.2f}s", file=sys.stderr, flush=True)
    return result


def evaluate(model_dir: str | Path):
    root = Path(model_dir).expanduser().resolve()
    assembly, scenario, motion = solve(root)
    checks = (
        _run_check(check_constraint_residuals,
            motion_result=motion,
            position_tolerance_m=1e-5,
            orientation_tolerance_rad=1e-5,
        ),
        _run_check(check_driver_tracking,
            motion_result=motion,
            scenario=scenario,
            joint_id=CRANK_JOINT,
            tolerance=0.03,
        ),
        _run_check(check_joint_limits, assembly=assembly, motion_result=motion),
        _run_check(check_trajectory,
            motion_result=motion,
            component_id=ROCKER,
            max_angular_speed_rad_s=0.7,
            max_angular_acceleration_rad_s2=1.0,
            min_path_length_m=0.0,
        ),
        _run_check(check_interference,
            assembly=assembly,
            motion_result=motion,
            component_pairs=COMPONENT_PAIRS,
            penetration_tolerance_m=0.0,
            sampling_scope="motion_result",
            max_sample_period_s=0.01,
            asset_root=root,
        ),
        _run_check(check_minimum_clearance,
            assembly=assembly,
            motion_result=motion,
            component_pairs=COMPONENT_PAIRS,
            minimum_allowed_clearance_m=0.0001,
            sampling_scope="motion_result",
            max_sample_period_s=0.01,
            asset_root=root,
        ),
        _run_check(check_continuous_interference,
            assembly=assembly,
            motion_result=motion,
            component_pairs=COMPONENT_PAIRS,
            asset_root=root,
            options=ContinuousInterferenceOptions(
                time_tolerance_s=1e-4,
                minimum_clearance_m=1e-4,
                max_iterations=32,
                max_subdivisions=20000,
            ),
        ),
    )
    hardware, collision_scope = _run_check(check_fixed_hardware, model_dir=root, assembly=assembly, motion=motion, group_pairs=COMPONENT_PAIRS)
    checks = (*checks, *hardware)
    negative_control = _run_check(detector_negative_control, model_dir=root, assembly=assembly, motion=motion, crank_id=CRANK, coupler_id=COUPLER)
    integrity = _run_check(check_assembly_integrity,
        assembly=assembly,
        motion_result=motion,
        asset_root=root,
        component_ids=(ROOT, CRANK, COUPLER, ROCKER),
        geometric_connection_pairs=(),
        containment_relations=(ContainmentRelation(
            relation_id="actuator.guard-envelope",
            contained_component_id=COUPLER,
            container_component_id=ROOT,
            axis=(0.0, 0.0, 1.0),
            min_position_m=-0.05,
            max_position_m=0.05,
            allowed_escape_tolerance_m=0.001,
        ),),
        sampling_scope="motion_result",
        require_single_network=True,
    )
    passed = (
        motion.status in {"completed", "completed_with_warnings"}
        and all(item.passed for item in checks)
        and integrity.passed
        and negative_control["passed"]
    )
    return assembly, motion, {
        "passed": passed,
        "collision_scope": collision_scope,
        "detector_negative_control": negative_control,
        "motion": motion.to_dict(),
        "checks": [item.to_dict() for item in checks],
        "assembly_integrity": integrity.to_dict(),
    }


def verify(model_dir: str | Path) -> dict:
    return evaluate(model_dir)[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--report", type=Path, help="Write full acceptance evidence without duplicating the motion arrays")
    args = parser.parse_args()
    try:
        result = verify(args.model_dir)
    except Exception as error:
        payload = error.to_dict() if isinstance(error, KinCheckError) else {
            "status": "failed", "error_type": type(error).__name__, "message": str(error)
        }
        print(json.dumps(payload, sort_keys=True))
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({k: v for k, v in result.items() if k != "motion"}, indent=2, sort_keys=True) + "\n")
    summary = {
        "passed": result["passed"],
        "collision_pair_count": result["collision_scope"]["physical_pair_count"],
        "detector_negative_control_passed": result["detector_negative_control"]["passed"],
        "motion_status": result["motion"]["status"],
        "sample_count": len(result["motion"]["sample_times_s"]),
        "integration_sample_count": len(result["motion"].get("integration_samples", ())),
        "checks": [
            {"check_id": item.get("check_id", item.get("operation", "unknown")), "passed": item["passed"], "issues": item.get("issues", []) if not item["passed"] else []}
            for item in result["checks"]
        ],
        "assembly_integrity": {
            "passed": result["assembly_integrity"]["passed"],
            "status": result["assembly_integrity"]["status"],
            "checked_sample_count": result["assembly_integrity"]["checked_sample_count"],
        },
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
