"""Independent reducer acceptance; no modeling imports or inferred gear ratios."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import median
from kincheckapi import assembly as assembly_api, cadir, checks, export, kinematics, scenario
from kincheckapi.errors import KinCheckError

CASE_DIR = Path(__file__).resolve().parents[1]
CASE_NAME = 'compact_two_stage_planetary_reducer'
ROOT_ID = 'compact_two_stage_planetary_reducer'
EXPECTED_RATIO = 20.0
INPUT_ID = 'input_shaft_revolute'
OUTPUT_ID = 'stage2_carrier_revolute'
MESH_IDS = ('stage1_sun_planet_1_external_mesh', 'stage1_ring_planet_1_internal_mesh', 'stage1_sun_planet_2_external_mesh', 'stage1_ring_planet_2_internal_mesh', 'stage1_sun_planet_3_external_mesh', 'stage1_ring_planet_3_internal_mesh', 'stage2_sun_planet_1_external_mesh', 'stage2_ring_planet_1_internal_mesh', 'stage2_sun_planet_2_external_mesh', 'stage2_ring_planet_2_internal_mesh', 'stage2_sun_planet_3_external_mesh', 'stage2_ring_planet_3_internal_mesh')


def _joint_id(assembly, source_id):
    # Two explicit serialization contracts for the same declared source ID.
    candidates = (source_id, f"joint/{ROOT_ID}/{source_id}")
    matches = [name for name in candidates if assembly.get_joint(joint_id=name) is not None]
    if len(matches) != 1:
        raise ValueError(f"Expected one declared joint ID from {candidates}, found {matches}")
    return matches[0]


def evaluate(model_dir):
    root = Path(model_dir).expanduser().resolve()
    converted = cadir.convert_mjcf(xml_path=root / "scene.xml", mapping_path=root / "scene.mapping.json", asset_root=root)
    assembly = converted.assembly
    assembly_api.validate_assembly(assembly=assembly).raise_if_failed()
    assembly_api.validate_topology(assembly=assembly).raise_if_failed()
    input_id, output_id = _joint_id(assembly, INPUT_ID), _joint_id(assembly, OUTPUT_ID)
    condition = scenario.create_scenario(scenario_id=f"verify.{CASE_NAME}", assembly=assembly)
    condition = scenario.add_joint_speed_driver(scenario=condition, joint_id=input_id, speed_rad_s_or_m_s=8.0, start_time_s=0.0, end_time_s=1.0)
    condition = scenario.set_run_duration(scenario=condition, duration_s=1.0)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.02)
    # Leave the request list empty so the independent equation audit can inspect
    # every joint trajectory emitted by the model.
    motion = kinematics.solve_motion(scenario=condition)
    available = {item.constraint_id for item in assembly.constraints}
    required_meshes = tuple(name if name in available else f"joint/{ROOT_ID}/{name}" for name in MESH_IDS)
    suite = checks.run_checks(assembly=assembly, scenario=condition, motion_result=motion, checks=(
        checks.CheckSpec(check_id="transmission-ratio", check_type="transmission_ratio", parameters={"input_joint_id": input_id, "output_joint_id": output_id, "expected_ratio": EXPECTED_RATIO, "expected_direction": "same", "start_time_s": 0.1, "end_time_s": 1.0, "relative_tolerance": 1e-3}),
        checks.CheckSpec(check_id="mesh-equations", check_type="constraint_equation_residuals", parameters={"constraint_ids": required_meshes, "linear_tolerance_m": 1e-8, "angular_tolerance_rad": 1e-8}),
    ))
    ratio_report = suite.reports[0]
    measured = next((e.actual for e in ratio_report.evidence if e.key == "median_ratio"), None)
    output = next(t for t in motion.joint_trajectories if t.joint_id == output_id)
    summary = {"passed": suite.passed, "status": "passed" if suite.passed else "failed", "expected_ratio": EXPECTED_RATIO, "measured_ratio": measured, "motion_status": motion.status, "sample_count": len(motion.sample_times_s), "output_speed_rad_s": median(v for t,v in zip(output.times_s,output.velocities) if 0.1 <= t <= 1.0), "expected_mesh_count": len(MESH_IDS), "actual_mesh_count": len(assembly.constraints), "component_count": len(assembly.components), "joint_count": len(assembly.joints), "closure_count": len(assembly.closures), "source": str(root), "checks": suite.to_dict()}
    return assembly, motion, suite, summary


def verify(model_dir):
    """Return a public CheckSuiteReport; existing CLI/API contract is unchanged."""
    return evaluate(model_dir)[2]


def record(*, variant):
    root = CASE_DIR / f"model_{variant}"
    output = CASE_DIR / "output" / variant
    output.mkdir(parents=True, exist_ok=True)
    assembly, motion, suite, summary = evaluate(root)
    summary["expected_failure"] = variant == "before"
    package = export.motion_package(assembly=assembly, motion_result=motion, output_path=output / f"{CASE_NAME}.kincheck", asset_root=root, require_meshes=True, title=f"{CASE_NAME}: {variant}", metadata={"verification_passed": suite.passed, "expected_ratio": EXPECTED_RATIO})
    export.read_package(path=package.path)
    summary["motion_package"] = str(package.path)
    report_path = output / f"{CASE_NAME}.verification.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key:value for key,value in summary.items() if key != "checks"}, ensure_ascii=False, indent=2))
    if variant == "after":
        suite.raise_if_failed()
    elif suite.passed:
        raise AssertionError("Archived failure unexpectedly passed; inspect the baseline")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", nargs="?", type=Path, default=CASE_DIR / "model_after")
    args = parser.parse_args()
    try:
        _, _, suite, summary = evaluate(args.model_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if suite.passed else 1
    except KinCheckError as error:
        print(json.dumps(error.to_dict(), ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
