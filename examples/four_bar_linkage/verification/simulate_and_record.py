"""Rebuild, sweep, and record the four-bar optimization evidence.

The native KinCheckAPI solve runs both an integration smoke test and a driven
full revolution. An independently constructed planar four-bar sweep is also
retained for deterministic clearance validation, with its source explicitly
recorded. Native closure residuals and drive travel are reported separately.
"""

from __future__ import annotations

from dataclasses import replace
import json
import math
import os
from pathlib import Path
import sys

CASE_DIR = Path(__file__).resolve().parents[1]
KINCHECKAPI_SRC = Path(
    os.environ.get("KINCHECKAPI_SRC", str(CASE_DIR.parents[1] / "src"))
)
sys.path.insert(0, str(KINCHECKAPI_SRC))
sys.path.insert(0, str(CASE_DIR / "verification"))
sys.path.insert(0, str(CASE_DIR / "model_after" / "source"))

from kincheckapi import export
from kincheckapi.cadir import convert_mjcf
from kincheckapi.clearance import check_interference
from kincheckapi.kinematics import solve_motion
from kincheckapi.scenario import (
    add_joint_speed_driver,
    create_scenario,
    set_run_duration,
    set_sample_period,
)

from collision_policy import COLLISION_EXCLUSION_COMPONENT_PAIRS  # noqa: E402
from four_bar_reference import (  # noqa: E402
    ROOT_ID,
    COUPLER_ID,
    CRANK_ID,
    ROCKER_ID,
    CRANK_JOINT,
    # Preserve the import used by simulate_before_optimization.py.
    build_reference_motion as _closed_form_motion,
)
from dimensions import (  # noqa: E402
    COUPLER_GEOMETRY_Z_OFFSET,
    GROUND_GEOMETRY_Z_OFFSET,
)


MJCF_DIR = CASE_DIR / "model_after"
OUT_DIR = CASE_DIR / "output" / "after"
XML_PATH = MJCF_DIR / "four_bar_linkage.xml"
MAPPING_PATH = MJCF_DIR / "four_bar_linkage.mapping.json"
PACKAGE_PATH = OUT_DIR / "four_bar_linkage_full_cycle.kincheck"
EVIDENCE_PATH = OUT_DIR / "four_bar_linkage.optimization.json"


def _native_solve(assembly):
    """Check the authored initial assembly without driving a joint."""

    scenario = create_scenario(scenario_id="four_bar_native_smoke", assembly=assembly)
    scenario = set_run_duration(scenario=scenario, duration_s=0.02)
    scenario = set_sample_period(scenario=scenario, period_s=0.01)
    return solve_motion(scenario=scenario)


def _native_driven_solve(assembly):
    """Run the native solver for the unchanged ten-second crank revolution."""

    scenario = create_scenario(scenario_id="four_bar_native_driven_probe", assembly=assembly)
    scenario = set_run_duration(scenario=scenario, duration_s=10.0)
    scenario = set_sample_period(scenario=scenario, period_s=0.1)
    scenario = add_joint_speed_driver(
        scenario=scenario,
        joint_id=CRANK_JOINT,
        speed_rad_s_or_m_s=2.0 * math.pi / 10.0,
        start_time_s=0.0,
        end_time_s=10.0,
    )
    return solve_motion(scenario=scenario)


def _clearance_summary(report) -> dict[str, object]:
    """Keep the shared JSON layout used by both example recording scripts."""

    return {
        "status": report.status,
        "passed": report.passed,
        "checked_pairs": report.checked_component_pair_count,
        "checked_samples": report.checked_sample_count,
        "event_count": len(report.events),
        "maximum_penetration_depth_m": report.maximum_penetration_depth_m,
        "first_failure_time_s": report.first_failure_time_s,
        "issue_codes": sorted({item.code for item in report.issues}),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 1. Load the same MJCF, mapping, and mesh assets.
    converted = convert_mjcf(
        xml_path=XML_PATH,
        mapping_path=MAPPING_PATH,
        asset_root=MJCF_DIR,
    )
    assembly = converted.assembly

    # 2. Record native initial-pose and driven-motion evidence.
    native = _native_solve(assembly)
    native_driven = _native_driven_solve(assembly)
    native_crank = next(
        item for item in native_driven.joint_trajectories if item.joint_id == CRANK_JOINT
    )

    # 3. Export and read back the independent reference trajectory.
    motion = _closed_form_motion(assembly.assembly_id)
    package = export.motion_package(
        assembly=assembly,
        motion_result=motion,
        output_path=PACKAGE_PATH,
        asset_root=MJCF_DIR,
        title="CADIR four-bar optimization full revolution",
        require_meshes=True,
        metadata={
            "source_mjcf": str(XML_PATH),
            "source_mapping": str(MAPPING_PATH),
            "optimization_iteration": "ground-axial-layer-and-joint-interface-policy",
        },
    )
    roundtrip_motion = export.read_package(path=PACKAGE_PATH).motion_result

    # 4. Run all three existing clearance checks on that reference trajectory.
    baseline_assembly = replace(assembly, collision_exclusions=())
    baseline = check_interference(
        assembly=baseline_assembly,
        motion_result=roundtrip_motion,
        asset_root=MJCF_DIR,
    )
    optimized = check_interference(
        assembly=assembly,
        motion_result=roundtrip_motion,
        asset_root=MJCF_DIR,
    )
    non_adjacent = check_interference(
        assembly=assembly,
        motion_result=roundtrip_motion,
        component_pairs=((ROOT_ID, COUPLER_ID), (CRANK_ID, ROCKER_ID)),
        asset_root=MJCF_DIR,
    )

    # 5. Preserve the output schema and distinguish native/reference evidence.
    evidence = {
        "source": {
            "model": str(XML_PATH),
            "mapping": str(MAPPING_PATH),
            "kincheck": str(PACKAGE_PATH),
            "package_bytes": package.path.stat().st_size,
            "package_sha256": package.sha256,
        },
        "model_change": {
            "ground_geometry_z_offset_mm": GROUND_GEOMETRY_Z_OFFSET,
            "coupler_geometry_z_offset_mm": COUPLER_GEOMETRY_Z_OFFSET,
            "collision_exclusion_component_pairs": [list(pair) for pair in COLLISION_EXCLUSION_COMPONENT_PAIRS],
            "collision_exclusion_group_pairs": [list(pair) for pair in assembly.collision_exclusions],
        },
        "native_solve": {
            "status": native.status,
            "sample_count": len(native.sample_times_s),
            "issue_codes": sorted({item.code for item in native.issues}),
        },
        "native_driven_probe": {
            "status": native_driven.status,
            "sample_count": len(native_driven.sample_times_s),
            "issue_codes": sorted({item.code for item in native_driven.issues}),
            "max_closure_position_residual_m": max(
                (item.position_residual_m for item in native_driven.closure_residuals), default=None,
            ),
            "max_closure_orientation_residual_rad": max(
                (item.orientation_residual_rad for item in native_driven.closure_residuals), default=None,
            ),
            "crank_travel_rad": native_crank.positions[-1] - native_crank.positions[0],
            "expected_crank_travel_rad": 2.0 * math.pi,
        },
        "closed_form_motion": {
            "status": motion.status,
            "sample_count": len(motion.sample_times_s),
            "max_closure_position_residual_m": max(
                (item.position_residual_m for item in motion.closure_residuals),
                default=0.0,
            ),
            "backend_id": motion.backend_id,
        },
        "clearance_before_interface_policy": _clearance_summary(baseline),
        "clearance_after_model_optimization": _clearance_summary(optimized),
        "non_adjacent_collision_regression": _clearance_summary(non_adjacent),
    }
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
