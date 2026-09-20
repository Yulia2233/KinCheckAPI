"""Archive completed static experiments, including their failed rating checks."""

import argparse
from pathlib import Path
from dataclasses import replace
import json
from kincheckapi.cadir import convert_mjcf
from kincheckapi.dynamics import (
    measure_package_physics,
    build_dynamics_model,
    compile_dynamics_model,
    StaticResult,
    check_static_load_limits,
)
from kincheckapi.export import motion_package, read_package, validate_package
from kincheckapi.result import MotionResult, Trajectory
from kincheckapi.visualization import export_motion_viewer


def archive(model_dir, verification_path, output_dir):
    root = Path(model_dir).resolve()
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = json.loads(Path(verification_path).read_text())
    assert report["passed"], report["issues"]
    manifest = measure_package_physics(package_path=root / "product.scadpkg")
    adapter = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    model = build_dynamics_model(assembly=adapter.assembly, manifest=manifest)
    compilation = compile_dynamics_model(model=model)
    cases = report["evidence"]["cases"]
    results = tuple(StaticResult.from_dict(c["result"]) for c in cases)
    checks = tuple(
        replace(
            check_static_load_limits(
                result=r, limits={next(iter(r.generalized_holding)): rating}
            ),
            model_sha256=model.content_hash,
            result_index=index,
        )
        for index, r in enumerate(results)
        for rating in (20.0, 35.0)
    )
    times = tuple(float(i) for i in range(len(results)))
    motion = MotionResult(
        scenario_id="E01-static-cases",
        assembly_id=model.assembly.assembly_id,
        status="completed",
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        trajectories=tuple(
            Trajectory(
                component_id=cid,
                times_s=times,
                poses=tuple(r.component_poses[cid] for r in results),
            )
            for cid in model.component_properties
        ),
        backend_id="analytic_tree_statics",
        backend_version="0.6.0",
        metadata={
            "component_result_scope": "all",
            "playback_coordinate": "case index; not physical time",
            "scope": "discrete static poses only; no interpolated trajectory claim",
        },
    )
    package = out / "dynamics_loaded_arm.kincheck"
    motion_package(
        assembly=model.assembly,
        motion_result=motion,
        output_path=package,
        asset_root=root,
        require_meshes=True,
        dynamics_model=model,
        static_results=results,
        static_checks=checks,
        title="E01 " + report["evidence"]["variant"] + " — static cases",
        metadata={
            "scope": "three static poses with/without eccentric load",
            "geometry_and_conversion_passed": True,
            "actuator_limits_passed": all(c.passed for c in checks),
        },
    )
    validate_package(path=package).raise_if_failed()
    read = read_package(path=package)
    assert [r.to_dict() for r in read.static_results] == [r.to_dict() for r in results]
    assert read.dynamics_model.manifest.to_dict() == manifest.to_dict()
    assert [c.to_dict() for c in read.static_checks] == [c.to_dict() for c in checks]
    export_motion_viewer(
        assembly=model.assembly,
        motion_result=motion,
        output_dir=out / "viewer",
        asset_root=root,
        static_results=results,
        static_checks=checks,
        title="E01 " + report["evidence"]["variant"] + " static evidence",
    )
    (out / "physics-manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2) + "\n"
    )
    (out / "explicit-inertia.xml").write_text(compilation.model_xml + "\n")
    # Keep one complete all-pair ledger per pose, not two duplicate copies.
    geometry = []
    for i, c in enumerate(cases):
        if not c["eccentric"]:
            geometry.append(c.pop("geometry"))
        else:
            c.pop("geometry")
        c["geometry_index"] = i // 2
    report["evidence"]["geometry_by_pose"] = geometry
    report["evidence"]["engineering_actuator_limits_passed"] = all(
        c.passed for c in checks
    )
    report["evidence"]["package_roundtrip_passed"] = True
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "roundtrip.json").write_text(
        json.dumps(
            {
                "passed": True,
                "manifest": True,
                "static_results": True,
                "static_checks": True,
                "package": str(package),
                "actuator_limits_passed": all(c.passed for c in checks),
            },
            indent=2,
        )
        + "\n"
    )
    print(package)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("model_dir")
    p.add_argument("verification_json")
    p.add_argument("output_dir")
    args = p.parse_args()
    archive(args.model_dir, args.verification_json, args.output_dir)
