"""Review regressions: re-signed archives must still prove their physics."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from kincheckapi.dynamics import (
    Payload,
    PhysicsError,
    build_dynamics_model,
    solve_static_equilibrium,
)
from kincheckapi.export import motion_package, read_package, validate_package
from kincheckapi.errors import MotionPackageError
from kincheckapi.physics_package import physics_document
from kincheckapi.result import MotionResult, Trajectory
from test_physics_v060 import arm, measured, request


def single_frame(model, result):
    return MotionResult(
        scenario_id="static",
        assembly_id=model.assembly.assembly_id,
        status="completed",
        start_time_s=5.0,
        end_time_s=5.0,
        sample_times_s=(5.0,),
        trajectories=tuple(
            Trajectory(component_id=cid, times_s=(5.0,), poses=(pose,))
            for cid, pose in result.component_poses.items()
        ),
    )


def write_case(path, model, results):
    motion_package(
        assembly=model.assembly,
        motion_result=single_frame(model, results[0]),
        output_path=path,
        dynamics_model=model,
        static_results=results,
    )


def rewrite_physics(path, change):
    with zipfile.ZipFile(path) as archive:
        members = {n: archive.read(n) for n in archive.namelist()}
    doc = json.loads(members["physics.json"])
    change(doc)
    members["physics.json"] = json.dumps(doc).encode()
    manifest = json.loads(members["manifest.json"])
    for entry in manifest["files"]:
        if entry["path"] == "physics.json":
            entry.update(
                bytes=len(members["physics.json"]),
                sha256=hashlib.sha256(members["physics.json"]).hexdigest(),
            )
    members["manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for n, data in members.items():
            archive.writestr(n, data)


MUTATIONS = {
    "residual": lambda r: r["body_residuals"]["arm"]["force_n"].__setitem__(0, 100.0),
    "holding": lambda r: r["generalized_holding"].__setitem__("j", 100.0),
    "support_total": lambda r: r["support_wrench"]["force_n"].__setitem__(2, 100.0),
    "support_individual": lambda r: r["support_wrench"]["individual"]["base"][
        "force_n"
    ].__setitem__(2, 100.0),
    "reaction": lambda r: r["joint_reactions"]["j"]["force_n"].__setitem__(0, 100.0),
    "load": lambda r: r["load_wrenches"][0]["force_n"].__setitem__(2, 100.0),
}


@pytest.mark.parametrize("channel", MUTATIONS)
def test_export_rejects_forged_completed_channels(tmp_path, channel):
    from kincheckapi.dynamics import StaticResult

    model = arm()
    r = solve_static_equilibrium(model=model, request=request())
    raw = r.to_dict()
    MUTATIONS[channel](raw)
    bad = StaticResult.from_dict(raw)
    with pytest.raises(PhysicsError):
        write_case(tmp_path / "bad.kincheck", model, (bad,))


@pytest.mark.parametrize("channel", MUTATIONS)
def test_read_rechecks_physics_even_when_member_hash_is_updated(tmp_path, channel):
    model = arm()
    r = solve_static_equilibrium(model=model, request=request())
    path = tmp_path / "resigned.kincheck"
    write_case(path, model, (r,))
    rewrite_physics(path, lambda d: MUTATIONS[channel](d["static_results"][0]))
    assert not validate_package(path=path).passed
    with pytest.raises(MotionPackageError):
        read_package(path=path)


def test_export_rejects_result_from_different_mass_model(tmp_path):
    light = arm()
    r = solve_static_equilibrium(model=light, request=request())
    heavy = build_dynamics_model(
        assembly=light.assembly,
        component_properties={
            **light.component_properties,
            "arm": replace(light.component_properties["arm"], mass_kg=200.0),
        },
    )
    with pytest.raises(PhysicsError):
        write_case(tmp_path / "mixed.kincheck", heavy, (r,))


def test_read_recomputes_after_model_and_binding_are_replaced(tmp_path):
    light = arm()
    r = solve_static_equilibrium(model=light, request=request())
    heavy = build_dynamics_model(
        assembly=light.assembly,
        component_properties={
            **light.component_properties,
            "arm": replace(light.component_properties["arm"], mass_kg=200.0),
        },
    )
    heavy_result = solve_static_equilibrium(model=heavy, request=request())
    path = tmp_path / "mixed.kincheck"
    write_case(path, light, (r,))

    def change(doc):
        old_result = doc["static_results"][0]
        doc.update(physics_document(heavy, (heavy_result,)))
        if "model_sha256" in old_result:
            old_result["model_sha256"] = doc["static_results"][0]["model_sha256"]
        doc["static_results"] = [old_result]

    rewrite_physics(path, change)
    assert not validate_package(path=path).passed


def test_explicit_payload_identity_and_provenance_survive_repeated_roundtrip(tmp_path):
    original = arm()
    p = Payload(
        payload_id="instrument",
        component_id="arm",
        properties=replace(
            measured("arm", 0.25, (0.7, 0, 0)),
            source_ids=("measured/instrument",),
            provenance={"source": "calibration-2026-09", "revision": "r3"},
        ),
    )
    model = build_dynamics_model(
        assembly=original.assembly,
        component_properties=original.component_properties,
        payloads=(p,),
    )
    for i in range(2):
        result = solve_static_equilibrium(model=model, request=request())
        path = tmp_path / f"payload-{i}.kincheck"
        write_case(path, model, (result,))
        restored = read_package(path=path).dynamics_model
        assert restored.payloads == (p,)
        assert restored.component_properties["arm"].mass_kg == pytest.approx(2.25)
        assert restored.base_component_properties == original.component_properties
        with pytest.raises(PhysicsError):
            build_dynamics_model(
                assembly=restored.assembly,
                component_properties=restored.base_component_properties,
                payloads=(*restored.payloads, p),
            )
        model = restored


@pytest.mark.parametrize(
    "req", [request(mode="free"), request(multiple=True, individual=True)]
)
def test_truthful_failed_and_indeterminate_experiments_remain_archivable(tmp_path, req):
    model = arm()
    r = solve_static_equilibrium(model=model, request=req)
    assert not r.passed
    path = tmp_path / "failed.kincheck"
    write_case(path, model, (r,))
    restored = read_package(path=path)
    assert restored.static_results[0].to_dict() == r.to_dict()
    with zipfile.ZipFile(path) as z:
        assert not json.loads(z.read("physics.json"))["acceptance_passed"]


@pytest.mark.parametrize("mode", ["direct", "package"])
def test_three_static_cases_are_independent_of_one_motion_sample(tmp_path, mode):
    from kincheckapi.visualization import export_motion_viewer
    from viewer.kincheck_viewer import unpack_package

    model = arm()
    results = tuple(
        solve_static_equilibrium(model=model, request=request(a))
        for a in (0.0, 0.4, 1.0)
    )
    root = tmp_path / mode
    if mode == "direct":
        export_motion_viewer(
            assembly=model.assembly,
            motion_result=single_frame(model, results[0]),
            output_dir=root,
            static_results=results,
            expected_ratio=2.0,
        )
    else:
        path = tmp_path / "cases.kincheck"
        write_case(path, model, results)
        unpack_package(package_path=path, output_dir=root, expected_ratio=2.0)
    manifest = json.loads((root / "viewer.json").read_text())
    assert manifest["sample_count"] == 1
    assert manifest["physics_case_count"] == 3
    assert (
        manifest["physics"]["static_results"][2]["component_poses"]["arm"]
        != manifest["components"][0]["initial_pose"]
    )
    assert manifest["metrics"]["ratio_unit"] == ":1"


def test_direct_viewer_supplies_dimensionless_ratio_unit(tmp_path):
    from kincheckapi.visualization import export_motion_viewer

    model = arm()
    r = solve_static_equilibrium(model=model, request=request())
    export_motion_viewer(
        assembly=model.assembly,
        motion_result=single_frame(model, r),
        output_dir=tmp_path / "viewer",
        expected_ratio=2.0,
    )
    manifest = json.loads((tmp_path / "viewer/viewer.json").read_text())
    assert manifest["metrics"]["ratio_unit"] == ":1"


def test_read_rejects_changed_request_and_unbound_physics(tmp_path):
    model = arm()
    r = solve_static_equilibrium(model=model, request=request())
    for name, change in [
        (
            "request",
            lambda d: d["static_results"][0]["request"]["gravity"].__setitem__(
                "acceleration_m_s2", [0.0, 0.0, 0.0]
            ),
        ),
        ("unbound", lambda d: d["static_results"][0].pop("model_sha256")),
        (
            "legacy_physics",
            lambda d: d.__setitem__("schema_version", "kincheck.static/1.0"),
        ),
    ]:
        path = tmp_path / f"{name}.kincheck"
        write_case(path, model, (r,))
        rewrite_physics(path, change)
        assert not validate_package(path=path).passed


def test_restored_payloads_can_be_extended_without_counting_them_twice(tmp_path):
    original = arm()
    first = Payload(
        payload_id="first",
        component_id="arm",
        properties=replace(measured("arm", 0.25), source_ids=("first-source",)),
    )
    model = build_dynamics_model(
        assembly=original.assembly,
        component_properties=original.component_properties,
        payloads=(first,),
    )
    r = solve_static_equilibrium(model=model, request=request())
    path = tmp_path / "first.kincheck"
    write_case(path, model, (r,))
    restored = read_package(path=path).dynamics_model
    second = Payload(
        payload_id="second",
        component_id="arm",
        properties=replace(measured("arm", 0.5), source_ids=("second-source",)),
    )
    extended = build_dynamics_model(
        assembly=restored.assembly,
        component_properties=restored.base_component_properties,
        payloads=(*restored.payloads, second),
    )
    assert extended.component_properties["arm"].mass_kg == pytest.approx(2.75)
    assert extended.payloads == (first, second)


def test_binding_survives_integer_joint_limits_json_normalization(tmp_path):
    from kincheckapi.assembly import JointLimit

    original = arm()
    assembly = replace(
        original.assembly,
        joints=(replace(original.assembly.joints[0], limit=JointLimit(-1, 1)),),
    )
    model = build_dynamics_model(
        assembly=assembly, component_properties=original.component_properties
    )
    result = solve_static_equilibrium(model=model, request=request())
    path = tmp_path / "limits.kincheck"
    write_case(path, model, (result,))
    assert validate_package(path=path).passed
    assert read_package(path=path).static_results[0].model_sha256 == result.model_sha256


def test_read_rejects_forged_derived_pass_flag(tmp_path):
    model = arm()
    result = solve_static_equilibrium(model=model, request=request(mode="free"))
    path = tmp_path / "false-pass.kincheck"
    write_case(path, model, (result,))
    rewrite_physics(path, lambda d: d["static_results"][0].__setitem__("passed", True))
    assert not validate_package(path=path).passed


def test_direct_model_without_payloads_retains_constructor_compatibility(tmp_path):
    from kincheckapi.dynamics import DynamicsModel

    source = arm()
    model = DynamicsModel(
        assembly=source.assembly,
        component_properties=source.component_properties,
        body_properties=source.body_properties,
        occurrence_components=source.occurrence_components,
    )
    result = solve_static_equilibrium(model=model, request=request())
    path = tmp_path / "direct-model.kincheck"
    write_case(path, model, (result,))
    assert (
        read_package(path=path).dynamics_model.base_component_properties
        == source.component_properties
    )


def test_unbound_static_check_cannot_forge_acceptance(tmp_path):
    from kincheckapi.physics_types import PhysicsReport

    model = arm()
    result = solve_static_equilibrium(model=model, request=request())
    forged = PhysicsReport(
        operation="check_static_load_limits",
        status="passed",
        evidence={"j": {"actual": 999.0, "limit": 0.0, "unit": "N*m"}},
    )
    with pytest.raises(PhysicsError):
        motion_package(
            assembly=model.assembly,
            motion_result=single_frame(model, result),
            output_path=tmp_path / "forged-check.kincheck",
            dynamics_model=model,
            static_results=(result,),
            static_checks=(forged,),
        )


def test_bound_static_check_is_replayed_and_tamper_detected(tmp_path):
    from kincheckapi.physics_types import PhysicsReport
    from dataclasses import replace

    model = arm()
    result = solve_static_equilibrium(model=model, request=request())
    check = replace(
        __import__(
            "kincheckapi.dynamics", fromlist=["check_static_load_limits"]
        ).check_static_load_limits(result=result, limits={"j": 20.0}),
        model_sha256=model.content_hash,
        result_index=0,
    )
    path = tmp_path / "bound-check.kincheck"
    motion_package(
        assembly=model.assembly,
        motion_result=single_frame(model, result),
        output_path=path,
        dynamics_model=model,
        static_results=(result,),
        static_checks=(check,),
    )
    assert read_package(path=path).static_checks[0].passed
    rewrite_physics(
        path, lambda d: d["checks"][0]["evidence"]["j"].__setitem__("limit", 0.0)
    )
    assert not validate_package(path=path).passed


def test_static_check_pass_flag_cannot_contradict_replayed_report(tmp_path):
    from dataclasses import replace

    from kincheckapi.dynamics import check_static_load_limits

    model = arm()
    result = solve_static_equilibrium(model=model, request=request())
    check = replace(
        check_static_load_limits(result=result, limits={"j": 20.0}),
        model_sha256=model.content_hash,
        result_index=0,
    )
    path = tmp_path / "check-pass-flag.kincheck"
    motion_package(
        assembly=model.assembly,
        motion_result=single_frame(model, result),
        output_path=path,
        dynamics_model=model,
        static_results=(result,),
        static_checks=(check,),
    )
    rewrite_physics(path, lambda d: d["checks"][0].__setitem__("passed", False))
    assert not validate_package(path=path).passed
