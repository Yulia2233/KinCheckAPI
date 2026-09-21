"""Explicit inertial compilation and independent MuJoCo principal-frame readback."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Mapping
import numpy as np

from .assembly import _freeze_mapping
from .physics_mass import check_mass_properties, compare_properties, rotation
from .physics_types import (
    DynamicsModel,
    PhysicsReport,
    RigidBodyProperties,
    fail,
    issue,
    plain,
)
from .pose import Pose
from .statics import probe_dynamics_capabilities


@dataclass(frozen=True, kw_only=True)
class DynamicsCompilation:
    """Public inertial evidence, without an exposed mutable simulator handle."""

    backend: str
    backend_version: str
    model_xml: str
    body_properties: Mapping[str, RigidBodyProperties]
    source_sha256: str | None
    # Private handle used only for backend-specific regression comparisons.
    _compiled: Any = field(repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(
            self, "body_properties", _freeze_mapping(self.body_properties)
        )

    def to_dict(self):
        return {
            "backend": self.backend,
            "backend_version": self.backend_version,
            "xml_sha256": hashlib.sha256(self.model_xml.encode()).hexdigest(),
            "body_properties": {
                k: v.to_dict() for k, v in self.body_properties.items()
            },
            "source_sha256": self.source_sha256,
            "inertia_source": "explicit-principal-inertia-with-reconstruction",
            "backend_quaternion_order": "wxyz",
            "public_quaternion_order": "xyzw",
        }


def _principal_inertial_attributes(properties):
    import mujoco

    tensor = np.asarray(properties.inertia_com_kg_m2)
    values, axes = np.linalg.eigh(tensor)
    if np.linalg.det(axes) < 0:
        axes[:, -1] *= -1
    # Eigen reconstruction is a floating point operation.  The previous
    # absolute tolerance rejected perfectly valid metre-scale assemblies when
    # a near-zero product of principal axes accumulated a few ulps of error.
    # Keep the check strict, but scale it to the tensor magnitude.
    reconstruction = axes @ np.diag(values) @ axes.T
    scale = max(float(np.max(np.abs(tensor))), 1.0)
    if not np.allclose(reconstruction, tensor, rtol=1e-10, atol=scale * 1e-14):
        fail(
            "BACKEND-INERTIAL-MISMATCH",
            "Principal tensor reconstruction failed.",
            operation="compile_dynamics_model",
            objects=properties.source_ids,
        )
    quat = np.zeros(4)
    mujoco.mju_mat2Quat(quat, axes.reshape(9))
    fmt = lambda v: " ".join(format(float(x), ".17g") for x in v)
    return {
        "mass": format(properties.mass_kg, ".17g"),
        "pos": fmt(properties.com_m),
        "diaginertia": fmt(values),
        "quat": fmt(quat),
    }


def compile_dynamics_model(*, model: DynamicsModel) -> DynamicsCompilation:
    """Compile the actual assembly with explicit m/c/I for every rigid group."""
    op = "compile_dynamics_model"
    probe = probe_dynamics_capabilities(model=model, operation=op, backend="mujoco")
    if not probe.passed:
        fail(
            "CAPABILITY-UNAVAILABLE",
            "MuJoCo compilation is unavailable.",
            operation=op,
            status="capability_failed",
            evidence=probe.to_dict(),
        )
    checked = check_mass_properties(model=model)
    if not checked.passed:
        fail(
            "PHYSICS-SOURCE-CONFLICT",
            "Physical source validation failed.",
            operation=op,
            evidence=checked.to_dict(),
        )
    import mujoco
    from ._backends.solver_backend import compile_assembly

    try:
        handle = compile_assembly(
            assembly=model.assembly, rigid_body_properties=model.body_properties
        )
    except Exception as exc:
        fail(
            "BACKEND-COMPILE-FAILED",
            str(exc),
            operation=op,
            status="capability_failed",
            fix="Correct the reported assembly/backend limitation; do not substitute kinematic inertia.",
        )
    readback = {}
    for index, gid in enumerate(sorted(model.body_properties)):
        bid = mujoco.mj_name2id(handle.model, mujoco.mjtObj.mjOBJ_BODY, f"body_{index}")
        if bid < 1:
            fail(
                "BACKEND-INERTIAL-MISMATCH",
                "Compiled body identity is missing.",
                operation=op,
                objects=(gid,),
            )
        w, x, y, z = handle.model.body_iquat[bid]
        r = rotation(Pose(orientation_xyzw=(x, y, z, w)))
        tensor = r @ np.diag(handle.model.body_inertia[bid]) @ r.T
        readback[gid] = RigidBodyProperties(
            mass_kg=float(handle.model.body_mass[bid]),
            com_m=tuple(handle.model.body_ipos[bid]),
            inertia_com_kg_m2=tensor,
            frame_id=gid,
            source_kind="mjcf_explicit",
            source_ids=model.body_properties[gid].source_ids,
            provenance={
                "backend": "mujoco",
                "version": mujoco.__version__,
                "body_id": bid,
                "body_iquat_wxyz": list(handle.model.body_iquat[bid]),
                "principal_inertia_kg_m2": list(handle.model.body_inertia[bid]),
            },
        )
    compiled = DynamicsCompilation(
        backend="mujoco",
        backend_version=mujoco.__version__,
        model_xml=handle.model_xml,
        body_properties=readback,
        source_sha256=model.manifest.source_sha256 if model.manifest else None,
        _compiled=handle,
    )
    report = validate_physics_conversion(model=model, compilation=compiled)
    if not report.passed:
        fail(
            "BACKEND-INERTIAL-MISMATCH",
            "Compiled mass/COM/tensor differs from the physical model.",
            operation=op,
            status="failed",
            evidence=report.to_dict(),
        )
    return compiled


def validate_physics_conversion(
    *, model: DynamicsModel, compilation: DynamicsCompilation | None = None
) -> PhysicsReport:
    """Audit definition→occurrence→rigid-group→compiled-body conservation."""
    op = "validate_physics_conversion"
    checked = check_mass_properties(model=model)
    problems = list(checked.issues)
    if compilation is None:
        compilation = compile_dynamics_model(model=model)
    if set(compilation.body_properties) != set(model.body_properties):
        problems.append(
            issue("OCCURRENCE-COVERAGE-INCOMPLETE", "Compiled body set differs.", op)
        )
    if model.manifest and compilation.source_sha256 != model.manifest.source_sha256:
        problems.append(
            issue("PHYSICS-SOURCE-CONFLICT", "Compilation source hash differs.", op)
        )
    for gid, p in model.body_properties.items():
        if gid in compilation.body_properties:
            problems.extend(
                compare_properties(
                    compilation.body_properties[gid], p, operation=op, object_id=gid
                )
            )
    return PhysicsReport(
        operation=op,
        status="failed" if problems else "passed",
        issues=tuple(problems),
        evidence={
            **checked.evidence,
            "backend": compilation.to_dict(),
            "occurrence_components": dict(model.occurrence_components),
            "mass_atol_kg": 1e-10,
            "com_atol_m": 1e-10,
            "inertia_atol_kg_m2": 1e-14,
            "relative_tolerance": 1e-8,
        },
    )
