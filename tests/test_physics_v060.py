"""Independent SI/analytic expectations frozen from the v0.6.0 requirements."""

from dataclasses import replace
import json
import math
from pathlib import Path

import numpy as np
import pytest

from kincheckapi.assembly import (
    AssemblyModel,
    Component,
    Connector,
    ConnectorRef,
    Ground,
    Joint,
    Part,
)
from kincheckapi.dynamics import *
from kincheckapi.pose import Pose


def measured(cid, mass=2.0, com=(0.3, 0, 0)):
    return RigidBodyProperties(
        mass_kg=mass,
        com_m=com,
        inertia_com_kg_m2=((0.01, 0, 0), (0, 0.02, 0), (0, 0, 0.025)),
        frame_id=cid,
        source_kind="measured",
        source_ids=(cid,),
        provenance={"source": "independent test fixture"},
    )


def arm(joint_type="revolute", reversed_joint=False):
    # Joint local Z is world -Y; positive coordinate raises the +X arm.
    mount = Connector("pivot", Pose(orientation_xyzw=(2**-0.5, 0, 0, 2**-0.5)))
    refs = [ConnectorRef("ground", "pivot"), ConnectorRef("arm", "pivot")]
    if reversed_joint:
        refs.reverse()
    a = AssemblyModel(
        "bench",
        parts=(Part("p"),),
        components=(
            Component("ground", "p", connectors=(mount,)),
            Component("arm", "p", connectors=(mount,)),
        ),
        joints=(Joint("j", joint_type, *refs),),
        grounds=(Ground("ground"),),
    )
    return build_dynamics_model(
        assembly=a,
        component_properties={
            "ground": measured("ground", 1.0, (0, 0, 0)),
            "arm": measured("arm"),
        },
    )


def request(
    angle=0.0,
    mode="hold",
    gravity=(0, 0, -9.81),
    loads=(),
    multiple=False,
    individual=False,
):
    supports = (
        SupportSpec(
            support_id="base",
            component_id="ground",
            occurrence_id="ground",
            interface_name="interface.mount",
            evidence_source="analytic fixed foundation",
        ),
    )
    if multiple:
        supports += (replace(supports[0], support_id="base2", point_m=(0.1, 0, 0)),)
    return StaticRequest(
        gravity=GravityField(acceleration_m_s2=gravity),
        supports=supports,
        joint_positions={"j": angle},
        joint_modes={"j": mode},
        loads=loads,
        request_individual_support_reactions=individual,
    )


@pytest.mark.parametrize("angle", [0, math.pi / 6, math.pi / 3])
def test_pendulum_from_horizontal(angle):
    r = solve_static_equilibrium(model=arm(), request=request(angle))
    assert r.passed, r.to_dict()
    assert r.generalized_holding["j"] == pytest.approx(2 * 9.81 * 0.3 * math.cos(angle))
    assert r.support_wrench["force_n"] == pytest.approx((0, 0, 3 * 9.81))
    assert check_wrench_balance(result=r).passed
    assert (
        StaticResult.from_dict(json.loads(json.dumps(r.to_dict()))).to_dict()
        == r.to_dict()
    )


def test_slider_weight_reverse_gravity_zero_and_sign():
    m = arm("prismatic")
    # Slider axis is -Y, so gravity along +Y loads its scalar coordinate.
    for gravity, expected in [
        ((0, 9.81, 0), 19.62),
        ((0, -9.81, 0), -19.62),
        ((0, 0, 0), 0),
    ]:
        r = solve_static_equilibrium(model=m, request=request(gravity=gravity))
        assert r.generalized_holding["j"] == pytest.approx(expected)
    r = solve_static_equilibrium(model=arm(reversed_joint=True), request=request())
    assert r.generalized_holding["j"] == pytest.approx(-5.886)


def test_free_joint_does_not_silently_lock():
    r = solve_static_equilibrium(model=arm(), request=request(mode="free"))
    assert not r.passed and any(
        i.code.endswith("STATIC-NOT-EQUILIBRIUM") for i in r.issues
    )
    assert not check_wrench_balance(result=r).passed
    assert all(i.stage == "solve_static_equilibrium" for i in r.issues)


def test_wrench_frames_are_equivalent_and_include_offset():
    angle = math.pi / 6
    local = WrenchLoad(
        load_id="force",
        component_id="arm",
        force_n=(0, 0, -100),
        moment_nm=(0, -2, 0),
        point_m=(0.4, 0.04, 0),
        frame_id="arm",
        applied_by="test rig",
    )
    world = replace(
        local,
        frame_id="world",
        force_n=(50, 0, -100 * math.cos(angle)),
        point_m=(0.4 * math.cos(angle), 0.04, 0.2),
    )
    a = solve_static_equilibrium(model=arm(), request=request(angle, loads=(local,)))
    b = solve_static_equilibrium(model=arm(), request=request(angle, loads=(world,)))
    assert a.passed and b.passed
    assert a.generalized_holding["j"] == pytest.approx(b.generalized_holding["j"])
    assert a.generalized_holding["j"] == pytest.approx(5.886 * math.cos(angle) + 38)
    assert not check_static_load_limits(result=a, limits={"j": 20}).passed


def test_support_missing_nonunique_contact_and_modes():
    m = arm()
    assert not solve_static_equilibrium(
        model=m, request=replace(request(), supports=())
    ).passed
    r = solve_static_equilibrium(
        model=m, request=request(multiple=True, individual=True)
    )
    assert r.status == "indeterminate" and r.generalized_holding
    assert any(i.code.endswith("REACTION-NONUNIQUE") for i in r.issues)
    r = solve_static_equilibrium(model=m, request=request(multiple=True))
    assert r.passed and not r.support_wrench["individual_reactions_unique"]
    r = solve_static_equilibrium(
        model=m,
        request=replace(
            request(), supports=(replace(request().supports[0], kind="unilateral"),)
        ),
    )
    assert r.status == "capability_failed"
    assert (
        solve_static_equilibrium(
            model=m, request=replace(request(), joint_modes={})
        ).status
        == "validation_failed"
    )


def test_no_future_dynamics_or_missing_physics():
    assert probe_dynamics_capabilities(
        model=arm(), operation="solve_inverse_dynamics"
    ).passed
    assert not probe_dynamics_capabilities(
        model=None, operation="solve_static_equilibrium"
    ).passed
    with pytest.raises(PhysicsError):
        build_dynamics_model(assembly=arm().assembly)
    with pytest.raises(PhysicsError):
        Payload(
            payload_id="p",
            component_id="arm",
            cad_occurrence_id="cad",
            properties=measured("arm"),
        )


def test_tensor_rotation_parallel_axis_associativity():
    p = RigidBodyProperties(
        mass_kg=0.0471,
        com_m=(0.005, 0.01, 0.015),
        inertia_com_kg_m2=np.diag([5.1025e-6, 3.925e-6, 1.9625e-6]),
        frame_id="world",
        source_kind="measured",
        source_ids=("a",),
    )
    b = transform_mass_properties(
        properties=p, pose=Pose(position_m=(0.1, 0, 0)), frame_id="world"
    )
    aggregate = aggregate_mass_properties(properties=(p, b), frame_id="world")
    assert aggregate.mass_kg == pytest.approx(0.0942)
    assert aggregate.com_m == pytest.approx((0.055, 0.01, 0.015))
    assert np.diag(aggregate.inertia_com_kg_m2) == pytest.approx(
        [1.0205e-5, 2.4335e-4, 2.39425e-4]
    )
    rotated = transform_mass_properties(
        properties=p,
        pose=Pose(
            orientation_xyzw=(0, 0, math.sin(math.pi / 8), math.cos(math.pi / 8))
        ),
        frame_id="world",
    )
    assert rotated.inertia_com_kg_m2[0][1] == pytest.approx((5.1025e-6 - 3.925e-6) / 2)
    flat = aggregate_mass_properties(properties=(p, b, rotated), frame_id="world")
    nested = aggregate_mass_properties(
        properties=(aggregate, rotated), frame_id="world"
    )
    np.testing.assert_allclose(
        flat.inertia_com_kg_m2, nested.inertia_com_kg_m2, rtol=1e-12, atol=1e-16
    )


@pytest.mark.parametrize(
    "tensor",
    [
        np.diag([-1, 2, 2]),
        np.diag([1, 1, 3]),
        [[1, 1, 0], [0, 1, 0], [0, 0, 1]],
        np.full((3, 3), float("nan")),
    ],
)
def test_invalid_tensor(tensor):
    with pytest.raises(PhysicsError):
        replace(measured("p"), inertia_com_kg_m2=tensor)


def test_backend_explicit_inertia_round_trip():
    m = arm()
    c = compile_dynamics_model(model=m)
    assert validate_physics_conversion(model=m, compilation=c).passed
    assert (
        "diaginertia" in c.model_xml
        and 'mass="1" diaginertia="0.001' not in c.model_xml
    )
    bad = dict(c.body_properties)
    bad["arm"] = replace(bad["arm"], mass_kg=2.1)
    assert not validate_physics_conversion(
        model=m, compilation=replace(c, body_properties=bad)
    ).passed


def test_brep_box_density_units_scaling():
    pytest.importorskip("simplecadapi")
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from simplecadapi.artifacts.brep import write_brep_bytes

    values = []
    for density, unit, scale in [
        (7850, "kg/m3", 1),
        (7.85e-6, "kg/mm^3", 1),
        (7850, "kg/m^3", 2),
    ]:
        values.append(
            measure_mass_properties(
                brep=write_brep_bytes(
                    BRepPrimAPI_MakeBox(10 * scale, 20 * scale, 30 * scale).Shape()
                ),
                material=PhysicsMaterial(
                    material_id="steel",
                    density=density,
                    density_unit=unit,
                    source="analytic",
                ),
                definition_id="box",
            )
        )
    p, q, big = values
    assert p.mass_kg == pytest.approx(0.0471, rel=1e-8, abs=1e-10)
    np.testing.assert_allclose(
        p.inertia_com_kg_m2,
        np.diag([5.1025e-6, 3.925e-6, 1.9625e-6]),
        rtol=1e-8,
        atol=1e-14,
    )
    np.testing.assert_allclose(
        p.inertia_com_kg_m2, q.inertia_com_kg_m2, rtol=1e-8, atol=1e-14
    )
    assert big.mass_kg == pytest.approx(8 * p.mass_kg)
    np.testing.assert_allclose(
        big.inertia_com_kg_m2,
        32 * np.asarray(p.inertia_com_kg_m2),
        rtol=1e-8,
        atol=1e-14,
    )


@pytest.mark.parametrize(
    "rho,unit", [(7850, ""), (-1, "kg/m3"), (float("nan"), "kg/m3")]
)
def test_invalid_density(rho, unit):
    with pytest.raises(PhysicsError):
        PhysicsMaterial(
            material_id="steel", density=rho, density_unit=unit, source="test"
        )


def test_backend_gravity_matches_independent_static_bench():
    import mujoco

    m = arm()
    c = compile_dynamics_model(model=m)
    native = c._compiled.model
    native.opt.gravity[:] = (0, 0, -9.81)
    for angle in (0, math.pi / 6, math.pi / 3):
        data = mujoco.MjData(native)
        data.qpos[0] = angle
        mujoco.mj_forward(native, data)
        assert data.qfrc_bias[0] == pytest.approx(
            5.886 * math.cos(angle), rel=1e-9, abs=1e-10
        )


def test_fixed_hardware_parallel_axis_and_ground_are_counted():
    m = arm()
    a = m.assembly
    bolt = Component(
        "bolt",
        "p",
        initial_pose=Pose(position_m=(0.4, 0, 0)),
        connectors=(Connector("bolt_mount"),),
    )
    a = replace(
        a,
        components=(*a.components, bolt),
        joints=(
            *a.joints,
            Joint(
                "bolt_fixed",
                "fixed",
                ConnectorRef("arm", "pivot"),
                ConnectorRef("bolt", "bolt_mount"),
            ),
        ),
    )
    # Fixed joints preserve authored offsets; the extra body is rigid hardware.
    model = build_dynamics_model(
        assembly=a,
        component_properties={
            **m.component_properties,
            "bolt": measured("bolt", 0.1, (0, 0, 0)),
        },
    )
    result = solve_static_equilibrium(model=model, request=request())
    assert result.generalized_holding["j"] == pytest.approx(5.886 + 0.1 * 9.81 * 0.4)
    assert result.support_wrench["force_n"][2] == pytest.approx(3.1 * 9.81)
    assert model.body_properties["arm"].mass_kg == pytest.approx(2.1)


def test_physics_package_and_old_package_roundtrip(tmp_path):
    from kincheckapi.export import motion_package, read_package, validate_package
    from kincheckapi.result import MotionResult, Trajectory

    model = arm()
    result = solve_static_equilibrium(model=model, request=request())
    motion = MotionResult(
        scenario_id="static",
        assembly_id=model.assembly.assembly_id,
        status="completed",
        start_time_s=0,
        end_time_s=0,
        sample_times_s=(0,),
        trajectories=tuple(
            Trajectory(component_id=cid, times_s=(0,), poses=(pose,))
            for cid, pose in result.component_poses.items()
        ),
    )
    target = tmp_path / "static.kincheck"
    motion_package(
        assembly=model.assembly,
        motion_result=motion,
        output_path=target,
        dynamics_model=model,
        static_results=(result,),
    )
    assert validate_package(path=target).passed
    read = read_package(path=target)
    assert read.static_results[0].to_dict() == result.to_dict()
    assert read.dynamics_model.component_properties["arm"].mass_kg == 2
    old = tmp_path / "old.kincheck"
    motion_package(assembly=model.assembly, motion_result=motion, output_path=old)
    assert read_package(path=old).dynamics_model is None


def test_manifest_hash_and_frame_tamper():
    from kincheckapi.physics_types import digest

    p = measured("d")
    o = PhysicsOccurrence(
        occurrence_id="o",
        definition_id="d",
        revision="1",
        content_hash="hash",
        pose_world=Pose(),
        properties=replace(p, frame_id="world"),
    )
    m = PhysicsManifest(
        definitions={"d": p},
        occurrences=(o,),
        source_path="measured",
        source_sha256="abc",
        producer={"test": "1"},
    )
    payload = m.to_dict()
    payload["occurrences"][0]["pose_world"]["position_m"][0] = 1000
    with pytest.raises(PhysicsError):
        PhysicsManifest.from_dict(payload)
    # Even recomputing a container hash cannot hide inconsistent frame transport.
    payload["sha256"] = digest({k: v for k, v in payload.items() if k != "sha256"})
    altered = PhysicsManifest.from_dict(payload)
    a = AssemblyModel(
        "one",
        parts=(Part("p"),),
        components=(Component("o", "p"),),
        grounds=(Ground("o"),),
    )
    model = build_dynamics_model(assembly=a, manifest=altered)
    assert not check_mass_properties(model=model).passed


def test_density_only_mjcf_rejected():
    root = (
        Path(__file__).resolve().parents[1] / "examples/guided_four_bar_actuator/model"
    )
    with pytest.raises(PhysicsError) as e:
        read_mjcf_mass_properties(
            xml_path=root / "scene.xml", mapping_path=root / "scene.mapping.json"
        )
    assert e.value.code.endswith("MESH-INERTIA-UNVERIFIED")
    assert e.value.operation == "read_mjcf_mass_properties"


def test_source_conflicts_and_payload_identity():
    m = arm()
    with pytest.raises(PhysicsError):
        build_dynamics_model(
            assembly=m.assembly,
            component_properties={**m.component_properties, "extra": measured("extra")},
        )
    with pytest.raises(PhysicsError):
        build_dynamics_model(
            assembly=m.assembly,
            component_properties=m.component_properties,
            payloads=(
                Payload(payload_id="p", component_id="arm", cad_occurrence_id="absent"),
            ),
        )
    load = WrenchLoad(
        load_id="x",
        component_id="absent",
        frame_id="world",
        point_m=(0, 0, 0),
        force_n=(0, 0, 0),
        moment_nm=(0, 0, 0),
        applied_by="test",
    )
    result = solve_static_equilibrium(model=m, request=request(loads=(load,)))
    assert result.status == "validation_failed"
    assert result.issues[0].stage == "solve_static_equilibrium"


def test_unique_support_reports_moment_at_its_reference_point():
    req = request()
    req = replace(req, supports=(replace(req.supports[0], point_m=(1, 0, 0)),))
    r = solve_static_equilibrium(model=arm(), request=req)
    support = r.support_wrench["individual"]["base"]
    assert support["reference_point_m"] == (1.0, 0.0, 0.0)
    # Total upward force at x=0 about x=1 gives +Y moment; arm compensation -Y.
    assert support["moment_nm"][1] == pytest.approx(3 * 9.81 - 5.886)


def test_unsupported_joint_and_closed_loop_are_operation_specific():
    from kincheckapi.assembly import Constraint, Closure

    m = arm()
    a = m.assembly
    closure = Closure(
        closure_id="loop",
        constraint=Constraint(
            "loop_constraint",
            ConnectorRef("ground", "pivot"),
            ConnectorRef("arm", "pivot"),
        ),
    )
    model = replace(m, assembly=replace(a, closures=(closure,)))
    report = solve_static_equilibrium(model=model, request=request())
    assert report.status == "capability_failed"
    assert all(i.stage == "solve_static_equilibrium" for i in report.issues)
    a = replace(a, joints=(replace(a.joints[0], joint_type="spherical"),))
    report = probe_dynamics_capabilities(
        model=replace(m, assembly=a), operation="solve_static_equilibrium"
    )
    assert any(i.code.endswith("JOINT-UNSUPPORTED") for i in report.issues)


def test_adapter_pose_metadata_survives_assembly_json():
    from kincheckapi.assembly import assembly_to_dict, assembly_from_dict

    p = measured("d", com=(0, 0, 0))
    occurrence = PhysicsOccurrence(
        occurrence_id="o",
        definition_id="d",
        revision="1",
        content_hash="x",
        pose_world=Pose(),
        properties=replace(p, frame_id="world"),
    )
    manifest = PhysicsManifest(
        definitions={"d": p},
        occurrences=(occurrence,),
        source_path="test",
        source_sha256="x",
        producer={"test": "1"},
    )
    assembly = AssemblyModel(
        "one",
        parts=(Part("p", metadata={"mesh_poses": {"d": (Pose(),)}}),),
        components=(Component("o", "p", metadata={"members": ("o",)}),),
        grounds=(Ground("o"),),
    )
    rebuilt = assembly_from_dict(
        data=json.loads(json.dumps(assembly_to_dict(assembly=assembly)))
    )
    assert check_mass_properties(
        model=build_dynamics_model(assembly=rebuilt, manifest=manifest)
    ).passed


def test_tampered_result_load_cannot_pass_balance():
    r=solve_static_equilibrium(model=arm(),request=request())
    records=[dict(v) for v in r.load_wrenches];records[0]['force_n']=(0,0,-1000)
    damaged=replace(r,load_wrenches=tuple(records))
    checked=check_wrench_balance(result=damaged)
    assert not checked.passed
    assert any(i.code.endswith('RESULT-INCONSISTENT') for i in checked.issues)
    with pytest.raises(PhysicsError):replace(r,generalized_holding={'j':float('nan')})


def test_two_link_subtree_equilibrium():
    m=arm();a=m.assembly
    angle=(2**-.5,0,0,2**-.5)
    first=replace(a.components[1],connectors=(*a.components[1].connectors,Connector('tip',Pose(position_m=(.3,0,0),orientation_xyzw=angle))))
    second=Component('arm2','p',initial_pose=Pose(position_m=(.3,0,0)),connectors=(Connector('root',Pose(orientation_xyzw=angle)),))
    a=replace(a,components=(a.components[0],first,second),joints=(*a.joints,Joint('j2','revolute',ConnectorRef('arm','tip'),ConnectorRef('arm2','root'))))
    m=build_dynamics_model(assembly=a,component_properties={'ground':measured('ground',1,(0,0,0)),'arm':measured('arm',1,(.15,0,0)),'arm2':measured('arm2',2,(.15,0,0))})
    req=replace(request(),joint_positions={'j':0,'j2':0},joint_modes={'j':'hold','j2':'locked'})
    r=solve_static_equilibrium(model=m,request=req)
    assert r.passed
    assert r.generalized_holding['j']==pytest.approx(9.81*(.15+2*.45))
    assert r.generalized_holding['j2']==pytest.approx(9.81*2*.15)
    assert check_wrench_balance(result=r).passed
