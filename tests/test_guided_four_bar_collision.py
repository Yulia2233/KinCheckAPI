"""Regression gates for the real example geometry and its acceptance scope."""
from itertools import combinations
from pathlib import Path

from examples.guided_four_bar_actuator.verification import verify
from examples.guided_four_bar_actuator.verification.collision_checks import check_fixed_hardware, detector_negative_control
from kincheckapi.cadir import convert_mjcf
from kincheckapi.clearance import check_interference
from kincheckapi.result import MotionResult, Trajectory

MODEL = Path(__file__).resolve().parents[1] / "examples/guided_four_bar_actuator/model"


def _initial_hold():
    assembly = convert_mjcf(xml_path=MODEL / "scene.xml", mapping_path=MODEL / "scene.mapping.json", asset_root=MODEL).assembly
    times = (0.0, 0.99, 1.0, 1.01, 2.0)
    motion = MotionResult(
        assembly_id=assembly.assembly_id, scenario_id="geometry-regression", status="completed",
        start_time_s=0, end_time_s=2, sample_times_s=times,
        trajectories=tuple(Trajectory(component_id=c.component_id, times_s=times, poses=(c.initial_pose,) * len(times)) for c in assembly.components),
    )
    return assembly, motion


def test_every_rigid_group_pair_is_checked_including_joint_neighbors():
    assembly, motion = _initial_hold()
    assert set(verify.COMPONENT_PAIRS) == set(combinations(sorted(c.component_id for c in assembly.components), 2))
    assert len(verify.COMPONENT_PAIRS) == 6
    assert not assembly.collision_exclusions
    report = check_interference(assembly=assembly, motion_result=motion, component_pairs=verify.COMPONENT_PAIRS,
                                start_time_s=0, end_time_s=0, asset_root=MODEL)
    assert report.passed, report.to_dict()


def test_physical_scope_includes_pins_and_fixed_guard():
    assembly, motion = _initial_hold()
    reports, scope = check_fixed_hardware(MODEL, assembly, motion, verify.COMPONENT_PAIRS)
    assert scope["physical_component_count"] == 9
    assert scope["physical_pair_count"] == 36
    assert len(scope["moving_physical_pairs"]) == 28
    assert len(scope["fixed_physical_pairs"]) == 8
    assert all(report.passed for report in reports)
    assert not scope["excluded_pairs"]


def test_real_coupler_overlap_is_detected_mid_motion():
    assembly, motion = _initial_hold()
    result = detector_negative_control(MODEL, assembly, motion, crank_id=verify.CRANK, coupler_id=verify.COUPLER)
    assert result["passed"], result
    assert result["sampled"]["status"] == "failed"
    assert result["continuous"]["status"] == "failed"
    assert any(e["confirmed"] for e in result["continuous"]["events"])
