"""MuJoCo-backed inverse/forward dynamics for scalar tree mechanisms."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Mapping

import numpy as np

from ._backends.solver_backend import (
    _group_values,
    _joint_values,
    _require_backend,
    compile_assembly,
)
from .assembly import JointType
from .dynamic_types import (
    ActuatorProfile,
    ActuatorSpec,
    ContactReport,
    ContactSpec,
    DynamicRequest,
    DynamicSample,
    ForwardDynamicsRequest,
    ForwardDynamicsResult,
    InverseDynamicsResult,
)
from .kinematics_geometry import forward_component_poses
from .physics_types import DynamicsModel, PhysicsReport, issue
from .pose import Pose, rotate_vector, transform_point
from .statics import probe_dynamics_capabilities


def _public_bindings(compiled, assembly, operation: str):
    bindings = {}
    for joint in assembly.joints:
        if joint.joint_type == JointType.FIXED:
            continue
        expression = compiled.joint_expressions.get(joint.joint_id)
        if expression is None or len(expression.coefficients) != 1:
            return None, issue(
                "JOINT-UNSUPPORTED",
                "Each dynamic joint must map to exactly one scalar backend coordinate.",
                operation,
                (joint.joint_id,),
                fix="Use one revolute or prismatic tree joint per backend coordinate.",
            )
        group_id, coefficient = next(iter(expression.coefficients.items()))
        if abs(abs(float(coefficient)) - 1.0) > 1e-9:
            return None, issue(
                "JOINT-UNSUPPORTED",
                "Dynamic effort mapping requires a unit public-to-backend joint coefficient.",
                operation,
                (joint.joint_id,),
            )
        bindings[joint.joint_id] = (group_id, float(coefficient), joint)
    return bindings, None


def _state_maps(request: DynamicRequest | ForwardDynamicsRequest):
    entries = request.states if isinstance(request, DynamicRequest) else request.initial_states
    return {s.joint_id: s for s in entries}


def _validate_state_coverage(model, states, bindings, operation):
    expected = set(bindings)
    actual = set(states)
    if actual != expected:
        return issue(
            "STATE-INVALID",
            "Dynamic state must provide exactly one position, velocity and acceleration for every movable scalar Joint.",
            operation,
            tuple(sorted(expected | actual)),
            actual=sorted(actual),
            expected=sorted(expected),
        )
    for joint_id, state in states.items():
        joint = bindings[joint_id][2]
        if joint.limit and not joint.limit.lower <= state.position <= joint.limit.upper:
            return issue(
                "STATE-INVALID",
                "Dynamic state exceeds the declared Joint limit.",
                operation,
                (joint_id,),
                actual=state.position,
                expected=[joint.limit.lower, joint.limit.upper],
                unit="rad" if joint.joint_type == JointType.REVOLUTE else "m",
            )
    return None


def _all_joint_positions(model, states):
    return {j.joint_id: float(states.get(j.joint_id).position if j.joint_id in states else 0.0) for j in model.assembly.joints}


def _body_id(runtime, mj_model, dynamics_model: DynamicsModel, gid: str) -> int:
    index = runtime.mj_name2id(mj_model, runtime.mjtObj.mjOBJ_BODY, f"body_{sorted(dynamics_model.body_properties).index(gid)}")
    if index < 1:
        raise ValueError(f"body for group {gid!r} is missing")
    return int(index)


def _apply_loads(*, compiled, data, model: DynamicsModel, loads, joint_positions, generalized_target=None):
    """Apply world-frame equivalent loads at current body COMs."""
    runtime = _require_backend()
    data.xfrc_applied[:] = 0.0
    if not loads:
        return {}
    poses = forward_component_poses(model.assembly, joint_positions)
    records = {}
    for load in loads:
        if load.component_id not in model.component_properties:
            raise ValueError(f"unknown load component {load.component_id!r}")
        if load.frame_id == "world":
            frame = Pose()
        elif load.frame_id in poses:
            frame = poses[load.frame_id]
        else:
            raise ValueError(f"unknown load frame {load.frame_id!r}")
        force = np.asarray(rotate_vector(pose=frame, vector=load.force_n), dtype=float)
        point = np.asarray(transform_point(pose=frame, point_m=load.point_m), dtype=float)
        moment = np.asarray(rotate_vector(pose=frame, vector=load.moment_nm), dtype=float)
        gid = compiled.component_groups[load.component_id]
        bid = _body_id(runtime, compiled.model, model, gid)
        com = np.asarray(data.xipos[bid], dtype=float)
        torque_at_com = moment + np.cross(point - com, force)
        data.xfrc_applied[bid, :3] += force
        data.xfrc_applied[bid, 3:] += torque_at_com
        if generalized_target is not None:
            runtime.mj_applyFT(compiled.model, data, force, moment, point, bid, generalized_target)
        records[load.load_id] = {
            "component_id": load.component_id,
            "frame_id": "world",
            "force_n": force.tolist(),
            "moment_nm": torque_at_com.tolist(),
            "point_m": point.tolist(),
        }
    return records


def _set_state(*, compiled, data, states, bindings):
    values = {}
    velocities = {}
    accelerations = {}
    for joint_id, (gid, coefficient, _joint) in bindings.items():
        state = states[joint_id]
        values[gid] = state.position / coefficient
        velocities[gid] = state.velocity / coefficient
        accelerations[gid] = state.acceleration / coefficient
    runtime = _require_backend()
    for gid, value in values.items():
        joint_name = compiled.group_joint_names[gid]
        jid = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, joint_name)
        data.qpos[int(compiled.model.jnt_qposadr[jid])] = value
        data.qvel[int(compiled.model.jnt_dofadr[jid])] = velocities[gid]
    runtime.mj_forward(compiled.model, data)
    for gid, value in values.items():
        joint_name = compiled.group_joint_names[gid]
        jid = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, joint_name)
        data.qacc[int(compiled.model.jnt_dofadr[jid])] = accelerations[gid]


def _set_accelerations(*, compiled, data, states, bindings):
    runtime = _require_backend()
    for joint_id, (gid, coefficient, _joint) in bindings.items():
        backend_joint = compiled.group_joint_names[gid]
        backend_id = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, backend_joint)
        data.qacc[int(compiled.model.jnt_dofadr[backend_id])] = states[joint_id].acceleration / coefficient


def solve_inverse_dynamics(*, model: DynamicsModel, request: DynamicRequest) -> InverseDynamicsResult:
    """Compute scalar joint effort for prescribed position/velocity/acceleration.

    The calculation is MuJoCo's inverse dynamics with explicit CADIR-derived
    mass/COM/inertia. It supports tree revolute/prismatic joints only.
    """
    operation = "solve_inverse_dynamics"
    probe = probe_dynamics_capabilities(model=model, operation=operation, backend="mujoco")
    if not probe.passed:
        return InverseDynamicsResult(status="capability_failed", issues=tuple(probe.issues), evidence=probe.evidence, request=request, model_sha256=model.content_hash if isinstance(model, DynamicsModel) else None)
    if not isinstance(request, DynamicRequest):
        return InverseDynamicsResult(status="validation_failed", issues=(issue("VALUE-INVALID", "request must be DynamicRequest.", operation),))
    try:
        compiled = compile_assembly(assembly=model.assembly, rigid_body_properties=model.body_properties)
        bindings, binding_issue = _public_bindings(compiled, model.assembly, operation)
        if binding_issue:
            return InverseDynamicsResult(status="capability_failed", issues=(binding_issue,), request=request, model_sha256=model.content_hash)
        states = _state_maps(request)
        state_issue = _validate_state_coverage(model, states, bindings, operation)
        if state_issue:
            return InverseDynamicsResult(status="validation_failed", issues=(state_issue,), request=request, model_sha256=model.content_hash)
        runtime = _require_backend()
        compiled.model.opt.gravity[:] = request.gravity.acceleration_m_s2
        data = runtime.MjData(compiled.model)
        _set_state(compiled=compiled, data=data, states=states, bindings=bindings)
        external_qfrc = np.zeros(compiled.model.nv, dtype=float)
        load_records = _apply_loads(compiled=compiled, data=data, model=model, loads=request.loads, joint_positions=_all_joint_positions(model, states), generalized_target=external_qfrc)
        runtime.mj_forward(compiled.model, data)
        _set_accelerations(compiled=compiled, data=data, states=states, bindings=bindings)
        runtime.mj_inverse(compiled.model, data)
        efforts = {}
        units = {}
        powers = {}
        for joint_id, (gid, coefficient, joint) in bindings.items():
            backend_joint = compiled.group_joint_names[gid]
            backend_id = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, backend_joint)
            qfrc = float(data.qfrc_inverse[int(compiled.model.jnt_dofadr[backend_id])] - external_qfrc[int(compiled.model.jnt_dofadr[backend_id])])
            effort = qfrc / coefficient
            efforts[joint_id] = effort
            units[joint_id] = "N*m" if joint.joint_type == JointType.REVOLUTE else "N"
            powers[joint_id] = effort * states[joint_id].velocity
        body_wrenches = {
            gid: {
                "force_n": data.xfrc_applied[_body_id(runtime, compiled.model, model, gid), :3].tolist(),
                "moment_nm": data.xfrc_applied[_body_id(runtime, compiled.model, model, gid), 3:].tolist(),
            }
            for gid in model.body_properties
        }
        return InverseDynamicsResult(
            status="completed",
            request=request,
            model_sha256=model.content_hash,
            generalized_efforts=efforts,
            generalized_units=units,
            joint_powers_w=powers,
            body_wrenches=body_wrenches,
            evidence={
                "backend": "mujoco",
                "backend_version": getattr(runtime, "__version__", "unknown"),
                "gravity_m_s2": list(request.gravity.acceleration_m_s2),
                "load_wrenches": load_records,
                "external_generalized_force_backend": external_qfrc.tolist(),
                "qfrc_inverse_backend": {gid: float(data.qfrc_inverse[int(compiled.model.jnt_dofadr[runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, compiled.group_joint_names[gid])])]) for gid in compiled.group_joint_names},
                "claim": "scalar tree inverse dynamics with rigid bodies",
            },
        )
    except Exception as exc:
        return InverseDynamicsResult(
            status="capability_failed" if "backend" in str(exc).lower() else "failed",
            issues=(issue("SOLVER-FAILED", str(exc), operation, fix="Inspect the dynamic model, state, and backend evidence before retrying."),),
            request=request,
            model_sha256=model.content_hash,
        )


def _add_motor_actuators(compiled, actuators: tuple[ActuatorSpec, ...], bindings, operation):
    root = ET.fromstring(compiled.model_xml)
    actuator_root = root.find("actuator")
    if actuator_root is None:
        actuator_root = ET.SubElement(root, "actuator")
    for spec in actuators:
        gid, coefficient, _joint = bindings[spec.joint_id]
        attributes = {
            "name": f"dynamic_motor_{spec.actuator_id}",
            "joint": compiled.group_joint_names[gid],
            "gear": f"{coefficient:.17g}",
            "ctrllimited": "true",
            "ctrlrange": f"{-spec.max_effort:.17g} {spec.max_effort:.17g}",
        }
        ET.SubElement(actuator_root, "motor", attributes)
    compiled.model_xml = ET.tostring(root, encoding="unicode")
    runtime = _require_backend()
    compiled.model = runtime.MjModel.from_xml_string(compiled.model_xml)


def _profile_by_id(profiles):
    return {p.actuator_id: p for p in profiles}


def _profile_effort(profile: ActuatorProfile, time_s: float) -> float:
    return profile.value_at(time_s)


def solve_forward_dynamics(*, model: DynamicsModel, request: ForwardDynamicsRequest) -> ForwardDynamicsResult:
    """Integrate a finite-actuator scalar tree and retain energy evidence."""
    operation = "solve_forward_dynamics"
    probe = probe_dynamics_capabilities(model=model, operation=operation, backend="mujoco")
    if not probe.passed:
        return ForwardDynamicsResult(status="capability_failed", issues=tuple(probe.issues), evidence=probe.evidence, request=request, model_sha256=model.content_hash if isinstance(model, DynamicsModel) else None)
    try:
        compiled = compile_assembly(assembly=model.assembly, rigid_body_properties=model.body_properties)
        bindings, binding_issue = _public_bindings(compiled, model.assembly, operation)
        if binding_issue:
            return ForwardDynamicsResult(status="capability_failed", issues=(binding_issue,), request=request, model_sha256=model.content_hash)
        states = _state_maps(request)
        state_issue = _validate_state_coverage(model, states, bindings, operation)
        if state_issue:
            return ForwardDynamicsResult(status="validation_failed", issues=(state_issue,), request=request, model_sha256=model.content_hash)
        for spec in request.actuators:
            if spec.joint_id not in bindings:
                return ForwardDynamicsResult(status="validation_failed", issues=(issue("ACTUATOR-INVALID", "Actuator references an unknown movable Joint.", operation, (spec.actuator_id, spec.joint_id)),), request=request, model_sha256=model.content_hash)
        _add_motor_actuators(compiled, request.actuators, bindings, operation)
        runtime = _require_backend()
        compiled.model.opt.gravity[:] = request.gravity.acceleration_m_s2
        data = runtime.MjData(compiled.model)
        _set_state(compiled=compiled, data=data, states=states, bindings=bindings)
        profiles = _profile_by_id(request.profiles)
        actuator_ids = {
            spec.actuator_id: runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_ACTUATOR, f"dynamic_motor_{spec.actuator_id}")
            for spec in request.actuators
        }
        spec_by_id = {spec.actuator_id: spec for spec in request.actuators}
        sample_times = [0.0]
        index = 1
        while index * request.sample_period_s < request.duration_s - 1e-12:
            sample_times.append(index * request.sample_period_s)
            index += 1
        if sample_times[-1] < request.duration_s - 1e-12:
            sample_times.append(request.duration_s)
        max_timestep = min(float(compiled.model.opt.timestep), request.sample_period_s / 5.0)
        compiled.model.opt.timestep = max_timestep
        samples = []
        previous_power = 0.0
        energy = 0.0
        peak_power = 0.0
        peak_effort = {spec.actuator_id: 0.0 for spec in request.actuators}
        def capture():
            group_positions, group_velocities = _group_values(compiled, data)
            joint_positions = _joint_values(compiled, group_positions)
            joint_velocities = _joint_values(compiled, group_velocities)
            joint_accelerations = {}
            for jid, (gid, coefficient, _joint) in bindings.items():
                backend = compiled.group_joint_names[gid]
                bid = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, backend)
                joint_accelerations[jid] = float(data.qacc[int(compiled.model.jnt_dofadr[bid])]) * coefficient
            actuator_efforts = {aid: float(data.ctrl[backend_id]) for aid, backend_id in actuator_ids.items()}
            return DynamicSample(time_s=float(data.time), joint_positions=joint_positions, joint_velocities=joint_velocities, joint_accelerations=joint_accelerations, actuator_efforts=actuator_efforts)
        for aid, backend_id in actuator_ids.items():
            data.ctrl[backend_id] = max(-spec_by_id[aid].max_effort, min(spec_by_id[aid].max_effort, _profile_effort(profiles[aid], 0.0)))
        samples.append(capture())
        for target_time in sample_times[1:]:
            while data.time < target_time - 1e-12:
                remaining = target_time - float(data.time)
                compiled.model.opt.timestep = min(max_timestep, remaining)
                current = float(data.time)
                for aid, backend_id in actuator_ids.items():
                    spec = spec_by_id[aid]
                    command = max(-spec.max_effort, min(spec.max_effort, _profile_effort(profiles[aid], current)))
                    data.ctrl[backend_id] = command
                    peak_effort[aid] = max(peak_effort[aid], abs(command))
                _apply_loads(compiled=compiled, data=data, model=model, loads=request.loads, joint_positions=_joint_values(compiled, _group_values(compiled, data)[0]))
                runtime.mj_step(compiled.model, data)
                if not all(math.isfinite(float(v)) for v in (*data.qpos, *data.qvel)):
                    return ForwardDynamicsResult(status="partial", issues=(issue("NONFINITE-STATE", "Forward dynamics produced a non-finite state.", operation, actual=float(data.time), unit="s"),), request=request, model_sha256=model.content_hash, samples=tuple(samples), energy_input_j=energy, peak_power_w=peak_power, peak_effort=peak_effort)
                command_power = sum(float(data.ctrl[actuator_ids[aid]]) * _joint_values(compiled, _group_values(compiled, data)[1]).get(spec_by_id[aid].joint_id, 0.0) / spec_by_id[aid].efficiency for aid in actuator_ids)
                dt = float(data.time) - (samples[-1].time_s if samples else 0.0)
                energy += 0.5 * (previous_power + command_power) * dt
                previous_power = command_power
                peak_power = max(peak_power, abs(command_power))
            samples.append(capture())
        issues = []
        for spec in request.actuators:
            if spec.max_speed is not None:
                max_seen = max((abs(s.joint_velocities.get(spec.joint_id, 0.0)) for s in samples), default=0.0)
                if max_seen > spec.max_speed + 1e-9:
                    issues.append(issue("ACTUATOR-SPEED-LIMIT", "Actuator speed limit was exceeded.", operation, (spec.actuator_id, spec.joint_id), actual=max_seen, expected=spec.max_speed, unit="rad/s or m/s"))
        return ForwardDynamicsResult(
            status="failed" if issues else "completed",
            issues=tuple(issues),
            request=request,
            model_sha256=model.content_hash,
            samples=tuple(samples),
            energy_input_j=energy,
            peak_power_w=peak_power,
            peak_effort=peak_effort,
            evidence={
                "backend": "mujoco",
                "sample_count": len(samples),
                "duration_s": request.duration_s,
                "gravity_m_s2": list(request.gravity.acceleration_m_s2),
                "finite_actuators": [a.to_dict() for a in request.actuators],
                "claim": "finite-actuator scalar tree forward dynamics",
            },
        )
    except Exception as exc:
        return ForwardDynamicsResult(status="failed", issues=(issue("SOLVER-FAILED", str(exc), operation, fix="Inspect the dynamic model, actuator profile, and backend evidence before retrying."),), request=request, model_sha256=model.content_hash)


def check_dynamic_load_limits(*, result: InverseDynamicsResult, limits: Mapping[str, float]) -> PhysicsReport:
    """Compare inverse-dynamics effort against declared per-joint limits."""
    operation = "check_dynamic_load_limits"
    if not isinstance(result, InverseDynamicsResult) or not isinstance(limits, Mapping):
        return PhysicsReport(operation=operation, status="validation_failed", issues=(issue("INPUT-INVALID", "result must be InverseDynamicsResult and limits must be a mapping.", operation),))
    problems = []
    if not result.passed:
        problems.append(issue("INPUT-RESULT-FAILED", "The inverse-dynamics result did not complete successfully.", operation, fix="Resolve the inverse-dynamics diagnostic and rerun the limit check."))
    for joint_id, limit in limits.items():
        actual = result.generalized_efforts.get(joint_id)
        try:
            limit_value = float(limit)
        except (TypeError, ValueError):
            limit_value = math.nan
        if actual is None or not math.isfinite(limit_value) or limit_value <= 0:
            problems.append(issue("LIMIT-INVALID", "Dynamic limit references a missing joint or is non-positive.", operation, (joint_id,)))
        elif abs(actual) > limit_value:
            problems.append(issue("DYNAMIC-LIMIT-EXCEEDED", "Required dynamic effort exceeds the declared limit.", operation, (joint_id,), actual=actual, expected=f"<= {limit_value}", unit=result.generalized_units.get(joint_id)))
    return PhysicsReport(operation=operation, status="failed" if problems else "passed", issues=tuple(problems), model_sha256=result.model_sha256, evidence={"limits": dict(limits), "efforts": dict(result.generalized_efforts)})


def check_dynamic_tracking(*, result: ForwardDynamicsResult, targets: Mapping[str, float], tolerance: Mapping[str, float] | float = 1e-3) -> PhysicsReport:
    """Check final forward-dynamics scalar positions against targets."""
    operation = "check_dynamic_tracking"
    if not isinstance(result, ForwardDynamicsResult) or not isinstance(targets, Mapping):
        return PhysicsReport(operation=operation, status="validation_failed", issues=(issue("INPUT-INVALID", "result must be ForwardDynamicsResult and targets must be a mapping.", operation),))
    if not result.samples:
        return PhysicsReport(operation=operation, status="validation_failed", issues=(issue("RESULT-EMPTY", "Forward dynamics has no samples.", operation),), model_sha256=result.model_sha256)
    final = result.samples[-1]
    problems = []
    invalid_input = False
    if not result.passed:
        problems.append(issue("INPUT-RESULT-FAILED", "The forward-dynamics result did not complete successfully.", operation, fix="Resolve the forward-dynamics diagnostic and rerun the tracking check."))
    errors = {}
    target_evidence = {}
    for joint_id, target in targets.items():
        if joint_id not in final.joint_positions:
            problems.append(issue("TARGET-INVALID", "Tracking target references an unknown joint.", operation, (joint_id,)))
            invalid_input = True
            continue
        try:
            target_value = float(target)
        except (TypeError, ValueError):
            problems.append(issue("TARGET-INVALID", "Tracking target must be a finite number.", operation, (joint_id,), actual=target, expected="finite float"))
            target_evidence[joint_id] = repr(target)
            invalid_input = True
            continue
        if not math.isfinite(target_value):
            target_evidence[joint_id] = repr(target_value)
            problems.append(issue("TARGET-INVALID", "Tracking target must be a finite number.", operation, (joint_id,), actual=repr(target_value), expected="finite float"))
            invalid_input = True
            continue
        target_evidence[joint_id] = target_value
        try:
            tol = float(tolerance[joint_id] if isinstance(tolerance, Mapping) and joint_id in tolerance else tolerance)
        except (TypeError, ValueError):
            tol = math.nan
        if not math.isfinite(tol) or tol < 0:
            problems.append(issue("TOLERANCE-INVALID", "Tracking tolerance must be finite and nonnegative.", operation, (joint_id,)))
            invalid_input = True
            continue
        error = final.joint_positions[joint_id] - target_value
        errors[joint_id] = error
        if abs(error) > tol:
            problems.append(issue("DYNAMIC-TRACKING-FAILED", "Forward dynamics final position exceeds tolerance.", operation, (joint_id,), actual=final.joint_positions[joint_id], expected=f"{target_value} +/- {tol}", unit="rad or m"))
    return PhysicsReport(operation=operation, status="validation_failed" if invalid_input else ("failed" if problems else "passed"), issues=tuple(problems), model_sha256=result.model_sha256, evidence={"final_positions": dict(final.joint_positions), "targets": target_evidence, "errors": errors})


def check_contact_capacity(*, contact: ContactSpec, force_n: tuple[float, float, float]) -> ContactReport:
    """Check a declared Coulomb contact capacity.

    The normal points in the direction of the applied compressive load. This
    is a capacity check, not a contact-force or impact solver.
    """
    if not isinstance(contact, ContactSpec):
        return ContactReport(status="validation_failed", issues=(issue("INPUT-INVALID", "contact must be ContactSpec.", "check_contact_capacity"),), contact_id="invalid")
    try:
        force = np.asarray(tuple(float(v) for v in force_n), dtype=float)
    except (TypeError, ValueError):
        force = np.asarray((), dtype=float)
    if force.shape != (3,) or not np.isfinite(force).all():
        return ContactReport(
            status="validation_failed",
            issues=(issue("CONTACT-INVALID", "force_n must be a finite 3-vector.", "check_contact_capacity", (contact.contact_id,)),),
            contact_id=contact.contact_id,
            evidence={"force_n": list(force_n) if hasattr(force_n, "__iter__") else force_n},
        )
    normal = np.asarray(contact.normal, dtype=float)
    normal_force = float(np.dot(force, normal))
    tangential = force - normal_force * normal
    tangential_force = float(np.linalg.norm(tangential))
    friction_limit = contact.friction_coefficient * max(normal_force, 0.0)
    utilization = {"friction": (tangential_force / friction_limit if friction_limit > 0 else math.inf if tangential_force > 0 else 0.0)}
    pressure = normal_force / contact.contact_area_m2 if contact.contact_area_m2 else None
    if contact.allowable_normal_force_n:
        utilization["normal_force"] = normal_force / contact.allowable_normal_force_n
    if pressure is not None and contact.allowable_pressure_pa:
        utilization["pressure"] = pressure / contact.allowable_pressure_pa
    problems = []
    if normal_force < 0:
        problems.append(issue("CONTACT-SEPARATION", "Applied load pulls away from the declared contact normal.", "check_contact_capacity", (contact.contact_id,), actual=normal_force, expected=">= 0", unit="N"))
    if tangential_force > friction_limit + 1e-12:
        problems.append(issue("FRICTION-LIMIT-EXCEEDED", "Tangential load exceeds the Coulomb friction capacity.", "check_contact_capacity", (contact.contact_id,), actual=tangential_force, expected=f"<= {friction_limit}", unit="N"))
    if contact.allowable_normal_force_n and normal_force > contact.allowable_normal_force_n + 1e-12:
        problems.append(issue("CONTACT-LOAD-LIMIT-EXCEEDED", "Normal contact load exceeds the declared limit.", "check_contact_capacity", (contact.contact_id,), actual=normal_force, expected=f"<= {contact.allowable_normal_force_n}", unit="N"))
    if pressure is not None and contact.allowable_pressure_pa and pressure > contact.allowable_pressure_pa + 1e-12:
        problems.append(issue("CONTACT-PRESSURE-LIMIT-EXCEEDED", "Contact pressure exceeds the declared limit.", "check_contact_capacity", (contact.contact_id,), actual=pressure, expected=f"<= {contact.allowable_pressure_pa}", unit="Pa"))
    return ContactReport(status="failed" if problems else "passed", issues=tuple(problems), contact_id=contact.contact_id, normal_force_n=normal_force, tangential_force_n=tangential_force, friction_limit_n=friction_limit, pressure_pa=pressure, utilization=utilization, evidence={"normal": list(contact.normal), "friction_coefficient": contact.friction_coefficient, "force_n": list(force_n), "capacity_claim": "Coulomb friction and declared normal/pressure limits"})


__all__ = [
    "solve_inverse_dynamics", "solve_forward_dynamics",
    "check_dynamic_load_limits", "check_dynamic_tracking", "check_contact_capacity",
]
