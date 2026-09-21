"""Tree scalar-joint equilibrium; no contact response or time integration."""

from __future__ import annotations

from dataclasses import replace
import importlib.metadata
from typing import Mapping
import numpy as np

from .assembly import JointType, build_kinematic_tree
from .kinematics_conventions import child_motion_sign
from .kinematics_geometry import forward_component_poses, forward_connector_poses
from .physics_mass import check_mass_properties, transform_mass_properties
from .physics_types import (
    DynamicsModel,
    PhysicsReport,
    StaticRequest,
    StaticResult,
    issue,
)
from .pose import Pose, rotate_vector, transform_point


def probe_dynamics_capabilities(
    *, model: DynamicsModel | None, operation: str, backend: str | None = None
) -> PhysicsReport:
    """Probe the requested operation/topology/data/backend combination."""
    problems = []
    versions = {}
    supported = {
        "solve_static_equilibrium",
        "solve_inverse_dynamics",
        "solve_forward_dynamics",
        "check_contact_capacity",
        "compile_dynamics_model",
        "validate_physics_conversion",
        "check_mass_properties",
    }
    if operation not in supported:
        problems.append(
            issue(
                "CAPABILITY-UNAVAILABLE",
                f"{operation} is outside the v0.6.3 dynamics capability contract.",
                operation,
                (operation,),
            )
        )
    requires_model = operation != "check_contact_capacity"
    if requires_model and (model is None or not isinstance(model, DynamicsModel)):
        problems.append(
            issue(
                "OCCURRENCE-COVERAGE-INCOMPLETE",
                "A physical model is required; kinematic data alone has no mass truth.",
                operation,
            )
        )
    elif requires_model:
        tree = build_kinematic_tree(assembly=model.assembly)
        if operation in ("solve_static_equilibrium", "solve_inverse_dynamics", "solve_forward_dynamics"):
            if (
                tree.closure_edges
                or model.assembly.closures
                or model.assembly.constraints
                or model.assembly.couplings
            ):
                problems.append(
                    issue(
                        "TOPOLOGY-UNSUPPORTED",
                        (
                            "Static per-joint solution requires a tree with no closure/coupling constraints."
                            if operation == "solve_static_equilibrium"
                            else "This per-joint dynamic solution requires a tree with no closure/coupling constraints."
                        ),
                        operation,
                        tuple(e.joint_id for e in tree.closure_edges),
                        fix="Request mass conversion only, or provide a future closed-loop reaction model.",
                    )
                )
            unsupported = [
                j.joint_id
                for j in model.assembly.joints
                if j.joint_type
                not in (JointType.FIXED, JointType.REVOLUTE, JointType.PRISMATIC)
            ]
            if unsupported:
                problems.append(
                    issue(
                        "JOINT-UNSUPPORTED",
                        "Only fixed/revolute/prismatic joints are supported.",
                        operation,
                        unsupported,
                    )
                )
        if set(model.component_properties) != {
            c.component_id for c in model.assembly.components
        }:
            problems.append(
                issue(
                    "OCCURRENCE-COVERAGE-INCOMPLETE",
                    "Physical component coverage is incomplete.",
                    operation,
                )
            )
    expected_backend = (
        "mujoco"
        if operation in (
            "compile_dynamics_model",
            "validate_physics_conversion",
            "solve_inverse_dynamics",
            "solve_forward_dynamics",
        )
        else "analytic_tree"
    )
    backend = backend or expected_backend
    if backend != expected_backend:
        problems.append(
            issue(
                "BACKEND-UNSUPPORTED",
                f"{operation} requires {expected_backend}.",
                operation,
                (backend,),
            )
        )
    if backend == "mujoco":
        try:
            import mujoco

            versions["mujoco"] = mujoco.__version__
        except ImportError:
            problems.append(
                issue(
                    "BACKEND-UNAVAILABLE",
                    "MuJoCo is not installed.",
                    operation,
                    ("mujoco",),
                )
            )
    return PhysicsReport(
        operation="probe_dynamics_capabilities",
        status="capability_failed" if problems else "passed",
        issues=tuple(problems),
        evidence={
            "requested_operation": operation,
            "backend": backend,
            "versions": versions,
            "static_topology": "tree",
            "joints": ["fixed", "revolute", "prismatic"],
            "contact_response": False,
            "inverse_dynamics": operation == "solve_inverse_dynamics" and not problems,
            "forward_dynamics": operation == "solve_forward_dynamics" and not problems,
        },
    )


def check_support(*, model: DynamicsModel, request: StaticRequest) -> PhysicsReport:
    """Check fixed support paths and CAD interface identity; no frictional stability claim."""
    op = "check_support"
    problems = []
    status = "validation_failed"
    tree = build_kinematic_tree(assembly=model.assembly)
    by_root = {}
    seen = set()
    occ = (
        {o.occurrence_id: o for o in model.manifest.occurrences}
        if model.manifest
        else {}
    )
    for s in request.supports:
        if s.support_id in seen:
            problems.append(
                issue("SUPPORT-INVALID", "Duplicate support ID.", op, (s.support_id,))
            )
        seen.add(s.support_id)
        gid = tree.component_groups.get(s.component_id)
        if gid not in tree.grounded_group_ids:
            problems.append(
                issue(
                    "SUPPORT-MISSING",
                    "Fixed support must attach to an explicitly grounded group.",
                    op,
                    (s.support_id, s.component_id),
                )
            )
            continue
        by_root.setdefault(gid, []).append(s.support_id)
        if s.frame_id != "world" and s.frame_id not in tree.component_groups:
            problems.append(
                issue(
                    "FRAME-INCOMPATIBLE",
                    "Support expression frame does not exist.",
                    op,
                    (s.support_id, s.frame_id),
                )
            )
        if model.manifest:
            o = occ.get(s.occurrence_id)
            if (
                o is None
                or model.occurrence_components.get(s.occurrence_id) != s.component_id
                or not o.interfaces.get(s.interface_name)
            ):
                problems.append(
                    issue(
                        "SUPPORT-MISSING",
                        "Support interface is absent on the declared CAD occurrence.",
                        op,
                        (s.support_id, s.occurrence_id, s.interface_name),
                        fix="Model the real mounting interface and bind its nonempty CAD face/region tag.",
                    )
                )
        elif not s.evidence_source:
            problems.append(
                issue(
                    "SUPPORT-MISSING",
                    "Analytical support requires an explicit evidence source.",
                    op,
                    (s.support_id,),
                )
            )
        if s.kind != "fixed":
            status = "capability_failed"
            problems.append(
                issue(
                    "SUPPORT-MODEL-UNSUPPORTED",
                    "Unilateral/frictional support stability requires contact response; v0.6.0 does not treat it as fixed.",
                    op,
                    (s.support_id,),
                    fix="Use a justified ideal fixed support, or a supported contact solver.",
                )
            )
    missing = set(tree.grounded_group_ids) - set(by_root)
    if not tree.grounded_group_ids or missing or tree.disconnected_group_ids:
        problems.append(
            issue(
                "SUPPORT-MISSING",
                "Every body needs a path to a declared supported ground.",
                op,
                tuple(sorted(missing | set(tree.disconnected_group_ids))),
            )
        )
    unique = all(len(v) == 1 for v in by_root.values()) and bool(by_root)
    if request.request_individual_support_reactions and not unique and not problems:
        status = "indeterminate"
        problems.append(
            issue(
                "REACTION-NONUNIQUE",
                "Multiple fixed mounting points do not uniquely determine individual reactions.",
                op,
                tuple(seen),
                fix="Request the total wrench or provide a calibrated compliance/load-sharing model.",
            )
        )
    return PhysicsReport(
        operation=op,
        status=status if problems else "passed",
        issues=tuple(problems),
        evidence={
            "supported_roots": by_root,
            "constraint_rank_by_root": {g: 6 for g in by_root},
            "individual_reactions_unique": unique,
            "geometric_mount_validation": "separate CAD geometry check required",
        },
    )


def solve_static_equilibrium(
    *, model: DynamicsModel, request: StaticRequest
) -> StaticResult:
    """Balance a given tree pose. Holding effort acts on B relative to A.

    Wrenches are world-expressed, force on the named receiver, moment about the
    reported reference point. Only locked/hold scalar DOFs can supply effort.
    """
    op = "solve_static_equilibrium"
    probe = probe_dynamics_capabilities(model=model, operation=op)
    if not probe.passed:
        return StaticResult(
            status="capability_failed",
            issues=tuple(replace(i, stage=op) for i in probe.issues),
            evidence=probe.evidence,
        )
    mass = check_mass_properties(model=model)
    if not mass.passed:
        return StaticResult(
            status="validation_failed",
            issues=tuple(replace(i, stage=op) for i in mass.issues),
        )
    support = check_support(model=model, request=request)
    # Nonunique individual reactions still permit total and holding evidence.
    fatal = [i for i in support.issues if not i.code.endswith("REACTION-NONUNIQUE")]
    if fatal:
        return StaticResult(
            status=support.status,
            issues=tuple(replace(i, stage=op) for i in fatal),
            evidence=support.evidence,
        )
    a = model.assembly
    tree = build_kinematic_tree(assembly=a)
    movable = {j.joint_id for j in a.joints if j.joint_type != JointType.FIXED}
    problems = []
    if set(request.joint_positions) != movable or set(request.joint_modes) != movable:
        problems.append(
            issue(
                "STATE-INVALID",
                "Provide exactly one position and explicit free/locked/hold mode for each movable joint.",
                op,
                tuple(sorted(movable)),
                actual={
                    "positions": list(request.joint_positions),
                    "modes": list(request.joint_modes),
                },
            )
        )
    for j in a.joints:
        q = request.joint_positions.get(j.joint_id, 0)
        if j.limit and not j.limit.lower <= q <= j.limit.upper:
            problems.append(
                issue(
                    "STATE-INVALID",
                    "Static position exceeds the joint limit.",
                    op,
                    (j.joint_id,),
                    actual=q,
                    expected=[j.limit.lower, j.limit.upper],
                    unit="rad" if j.joint_type == JointType.REVOLUTE else "m",
                )
            )
    ids = set(model.component_properties)
    load_ids = set()
    for load in request.loads:
        if (
            load.component_id not in ids
            or (load.frame_id != "world" and load.frame_id not in ids)
            or load.load_id in load_ids
        ):
            problems.append(
                issue(
                    "LOAD-INVALID",
                    "Unknown load receiver/frame or duplicate load identity.",
                    op,
                    (load.load_id, load.component_id, load.frame_id),
                )
            )
        load_ids.add(load.load_id)
    if problems:
        return StaticResult(status="validation_failed", issues=tuple(problems))
    poses = forward_component_poses(a, request.joint_positions)
    connectors = forward_connector_poses(a, request.joint_positions)
    ext = {gid: np.zeros(6) for gid in tree.group_components}
    load_records = []
    for cid, p in sorted(model.component_properties.items()):
        world = transform_mass_properties(
            properties=p, pose=poses[cid], frame_id="world"
        )
        force = p.mass_kg * np.asarray(request.gravity.acceleration_m_s2)
        point = np.asarray(world.com_m)
        wrench = np.r_[force, np.cross(point, force)]
        ext[tree.component_groups[cid]] += wrench
        load_records.append(
            {
                "load_id": "gravity/" + cid,
                "component_id": cid,
                "applied_by": "gravity",
                "frame_id": "world",
                "point_m": point.tolist(),
                "force_n": force.tolist(),
                "moment_nm": [0.0, 0.0, 0.0],
            }
        )
    for load in request.loads:
        frame = Pose() if load.frame_id == "world" else poses[load.frame_id]
        f = np.asarray(rotate_vector(pose=frame, vector=load.force_n))
        point = np.asarray(transform_point(pose=frame, point_m=load.point_m))
        torque = np.asarray(rotate_vector(pose=frame, vector=load.moment_nm))
        ext[tree.component_groups[load.component_id]] += np.r_[
            f, torque + np.cross(point, f)
        ]
        load_records.append(
            {
                "load_id": load.load_id,
                "component_id": load.component_id,
                "applied_by": load.applied_by,
                "frame_id": "world",
                "point_m": point.tolist(),
                "force_n": f.tolist(),
                "moment_nm": torque.tolist(),
            }
        )
    children = {g: [] for g in ext}
    for edge in tree.tree_edges:
        children[edge.parent_group_id].append(edge)
    subtree = {}

    def total(g):
        value = ext[g].copy()
        for e in children[g]:
            value += total(e.child_group_id)
        subtree[g] = value
        return value

    for root in tree.root_group_ids:
        total(root)
    holding = {}
    units = {}
    reactions = {}
    reaction_vectors = {}
    for e in tree.tree_edges:
        j = a.get_joint(joint_id=e.joint_id)
        frame = connectors[(j.connector_a.component_id, j.connector_a.connector_id)]
        other = connectors[(j.connector_b.component_id, j.connector_b.connector_id)]
        axis = np.asarray(rotate_vector(pose=frame, vector=(0, 0, 1)))
        origin = np.asarray(frame.position_m)
        other_axis = np.asarray(rotate_vector(pose=other, vector=(0, 0, 1)))
        delta = np.asarray(other.position_m) - origin
        error = np.linalg.norm(
            delta
            if j.joint_type == JointType.REVOLUTE
            else delta - axis * np.dot(delta, axis)
        )
        if (
            error > 1e-7
            or np.linalg.norm(np.cross(axis, other_axis)) > 1e-7
            or np.dot(axis, other_axis) < 0
        ):
            problems.append(
                issue(
                    "STATE-INVALID",
                    "Joint interfaces do not realize the requested ideal joint at this pose.",
                    op,
                    (j.joint_id,),
                    actual=float(error),
                    expected=1e-7,
                    unit="m",
                )
            )
        w = subtree[e.child_group_id]
        moment = w[3:] - np.cross(origin, w[:3])
        rotational = j.joint_type == JointType.REVOLUTE
        sign = child_motion_sign(
            joint=j,
            child_group_id=e.child_group_id,
            component_groups=tree.component_groups,
        )
        projection = float(np.dot(axis, moment if rotational else w[:3]))
        effort = -sign * projection
        units[j.joint_id] = "N*m" if rotational else "N"
        holding[j.joint_id] = effort
        r = -w.copy()
        if request.joint_modes[j.joint_id] == "free":
            if rotational:
                r[3:] += axis * projection
            else:
                r[:3] += axis * projection
                r[3:] += np.cross(origin, axis * projection)
            tolerance = (
                request.moment_tolerance_nm if rotational else request.force_tolerance_n
            )
            if abs(effort) > tolerance:
                problems.append(
                    issue(
                        "STATIC-NOT-EQUILIBRIUM",
                        "Free DOF cannot supply the required holding effort.",
                        op,
                        (j.joint_id,),
                        actual=effort,
                        expected=0,
                        unit=units[j.joint_id],
                        fix="Provide an explicit holding drive/lock or choose a true equilibrium pose.",
                    )
                )
        reaction_vectors[j.joint_id] = r
        reactions[j.joint_id] = {
            "force_n": r[:3].tolist(),
            "moment_nm": (r[3:] - np.cross(origin, r[:3])).tolist(),
            "reference_point_m": origin.tolist(),
            "frame_id": "world",
            "applied_to_group": e.child_group_id,
            "applied_by_group": e.parent_group_id,
            "opposite_pair_id": j.joint_id,
            "includes_holding_effort": request.joint_modes[j.joint_id] != "free",
            "unique": True,
        }
    residual = {g: v.copy() for g, v in ext.items()}
    for e in tree.tree_edges:
        r = reaction_vectors[e.joint_id]
        residual[e.child_group_id] += r
        residual[e.parent_group_id] -= r
    ground = np.zeros(6)
    per_root = {}
    individual = {}
    for root in tree.root_group_ids:
        r = -subtree[root]
        ground += r
        residual[root] += r
        per_root[root] = {
            "force_n": r[:3].tolist(),
            "moment_nm": r[3:].tolist(),
            "reference_point_m": [0.0, 0.0, 0.0],
        }
        mounts = [
            s for s in request.supports if tree.component_groups[s.component_id] == root
        ]
        if len(mounts) == 1:
            mount = mounts[0]
            frame = Pose() if mount.frame_id == "world" else poses[mount.frame_id]
            point = np.asarray(transform_point(pose=frame, point_m=mount.point_m))
            individual[mount.support_id] = {
                "force_n": r[:3].tolist(),
                "moment_nm": (r[3:] - np.cross(point, r[:3])).tolist(),
                "reference_point_m": point.tolist(),
                "frame_id": "world",
                "applied_to_group": root,
                "applied_by": "environment",
                "unique": True,
            }
    body_res = {}
    for gid, w in residual.items():
        body_res[gid] = {
            "force_n": w[:3].tolist(),
            "moment_nm": w[3:].tolist(),
            "reference_point_m": [0.0, 0.0, 0.0],
        }
        if (
            np.linalg.norm(w[:3]) > request.force_tolerance_n
            or np.linalg.norm(w[3:]) > request.moment_tolerance_nm
        ):
            problems.append(
                issue(
                    "STATIC-NOT-EQUILIBRIUM",
                    "Rigid body wrench is not balanced.",
                    op,
                    (gid,),
                    actual=body_res[gid],
                    expected={
                        "force_n": request.force_tolerance_n,
                        "moment_nm": request.moment_tolerance_nm,
                    },
                    unit="N;N*m",
                )
            )
    nonunique = [replace(i, stage=op) for i in support.issues]
    status = "failed" if problems else ("indeterminate" if nonunique else "completed")
    return StaticResult(
        model_sha256=model.content_hash,
        request=request,
        status=status,
        issues=tuple(problems + nonunique),
        generalized_holding=holding,
        generalized_units=units,
        joint_reactions=reactions,
        body_residuals=body_res,
        component_poses=poses,
        load_wrenches=tuple(load_records),
        support_wrench={
            "force_n": ground[:3].tolist(),
            "moment_nm": ground[3:].tolist(),
            "reference_point_m": [0.0, 0.0, 0.0],
            "frame_id": "world",
            "applied_by": "environment",
            "applied_to": "assembly",
            "unique_total": True,
            "individual_reactions_unique": support.evidence[
                "individual_reactions_unique"
            ],
            "by_ground_group": per_root,
            "individual": individual,
        },
        evidence={
            "gravity_m_s2": request.gravity.acceleration_m_s2,
            "joint_positions": dict(request.joint_positions),
            "joint_modes": dict(request.joint_modes),
            "total_mass_kg": sum(
                p.mass_kg for p in model.component_properties.values()
            ),
            "force_tolerance_n": request.force_tolerance_n,
            "moment_tolerance_nm": request.moment_tolerance_nm,
            "support": support.evidence,
            "scope": "rigid ideal joints; no contact stability or strength",
            "source_sha256": model.manifest.source_sha256 if model.manifest else None,
            "component_groups": dict(tree.component_groups),
        },
    )


def check_wrench_balance(
    *,
    result: StaticResult,
    force_tolerance_n: float = 0.01,
    moment_tolerance_nm: float = 0.001,
) -> PhysicsReport:
    """Accept only complete per-body force AND moment evidence."""
    from .physics_types import positive

    op = "check_wrench_balance"
    positive(force_tolerance_n, "force_tolerance_n", op)
    positive(moment_tolerance_nm, "moment_tolerance_nm", op)
    problems = []
    if not result.body_residuals or result.status not in (
        "completed",
        "completed_with_warnings",
    ):
        problems.append(
            issue(
                "STATIC-NOT-EQUILIBRIUM",
                "Static result is not complete and accepted.",
                op,
                actual=result.status,
            )
        )
    reconstructed = {g: np.zeros(6) for g in result.body_residuals}
    groups = result.evidence.get("component_groups", {})

    def world_wrench(record, point_key="reference_point_m"):
        f = np.asarray(record["force_n"])
        point = np.asarray(record[point_key])
        return np.r_[f, np.asarray(record["moment_nm"]) + np.cross(point, f)]

    try:
        if set(groups) != set(result.component_poses):
            raise ValueError("Missing component-to-body coverage")
        for load in result.load_wrenches:
            reconstructed[groups[load["component_id"]]] += world_wrench(load, "point_m")
        for reaction in result.joint_reactions.values():
            wrench = world_wrench(reaction)
            reconstructed[reaction["applied_to_group"]] += wrench
            reconstructed[reaction["applied_by_group"]] -= wrench
        for gid, support in result.support_wrench["by_ground_group"].items():
            reconstructed[gid] += world_wrench(support)
        for gid, wrench in reconstructed.items():
            reported = world_wrench(result.body_residuals[gid])
            delta = wrench - reported
            if (
                np.linalg.norm(delta[:3]) > force_tolerance_n
                or np.linalg.norm(delta[3:]) > moment_tolerance_nm
            ):
                problems.append(
                    issue(
                        "RESULT-INCONSISTENT",
                        "Reported balance differs from loads and paired reactions.",
                        op,
                        (gid,),
                        actual=wrench.tolist(),
                        expected=reported.tolist(),
                        unit="N;N*m",
                    )
                )
    except (KeyError, ValueError, TypeError) as exc:
        problems.append(
            issue(
                "RESULT-INCOMPLETE",
                str(exc),
                op,
                fix="Preserve all load, joint, body, and support references in the static result.",
            )
        )
    for gid, w in result.body_residuals.items():
        for key, unit, tolerance in [
            ("force_n", "N", force_tolerance_n),
            ("moment_nm", "N*m", moment_tolerance_nm),
        ]:
            value = float(np.linalg.norm(w[key]))
            if not np.isfinite(value) or value > tolerance:
                problems.append(
                    issue(
                        "STATIC-NOT-EQUILIBRIUM",
                        "Body balance residual exceeds its dimensional tolerance.",
                        op,
                        (gid,),
                        actual=value,
                        expected=tolerance,
                        unit=unit,
                    )
                )
    return PhysicsReport(
        operation=op,
        status="failed" if problems else "passed",
        issues=tuple(problems),
        evidence={
            "body_residuals": result.body_residuals,
            "force_tolerance_n": force_tolerance_n,
            "moment_tolerance_nm": moment_tolerance_nm,
        },
    )


def check_static_load_limits(
    *, result: StaticResult, limits: Mapping[str, float]
) -> PhysicsReport:
    """Compare scalar holding demands to positive N/N*m ratings; no stress claim."""
    from .physics_types import positive

    op = "check_static_load_limits"
    problems = []
    measurements = {}
    if not limits or not result.passed:
        problems.append(
            issue(
                "LOAD-LIMIT-UNAVAILABLE",
                "Require a completed static result and explicit nonempty ratings.",
                op,
            )
        )
    for jid, limit in limits.items():
        positive(limit, jid, op)
        if jid not in result.generalized_holding:
            problems.append(
                issue(
                    "LOAD-LIMIT-UNAVAILABLE",
                    "No holding demand for rated joint.",
                    op,
                    (jid,),
                )
            )
            continue
        value = abs(result.generalized_holding[jid])
        measurements[jid] = {
            "actual": value,
            "limit": limit,
            "unit": result.generalized_units[jid],
        }
        if value > limit:
            problems.append(
                issue(
                    "STATIC-LOAD-LIMIT",
                    "Required holding effort exceeds the specified rating.",
                    op,
                    (jid,),
                    actual=value,
                    expected=limit,
                    unit=result.generalized_units[jid],
                    fix="Increase the justified actuator rating or redesign the physical load path; do not change acceptance thresholds.",
                )
            )
    return PhysicsReport(
        operation=op,
        status="failed" if problems else "passed",
        issues=tuple(problems),
        evidence=measurements,
    )
