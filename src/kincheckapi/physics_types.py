"""Versioned SI physics contracts. Tensors are row-major about COM in frame_id.

No implicit material, mass, inertia, gravity, support, or joint locking defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np

from .assembly import AssemblyModel, _freeze_mapping
from .diagnostics import AgentReadableResult, Evidence, SimIssue
from .errors import KinCheckError
from .pose import Pose


def plain(value):
    if isinstance(value, Mapping):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, np.generic):
        return value.item()
    return value


def digest(value):
    return hashlib.sha256(
        json.dumps(
            plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


class PhysicsError(KinCheckError):
    """Invalid, unavailable, or conflicting physics input; never a placeholder."""

    def to_dict(self, *, include_traceback=False):
        value = super().to_dict(include_traceback=include_traceback)
        return {
            **value,
            "passed": False,
            "what_happened": self.message,
            "cause": self.details.get("cause", self.code),
            "how_to_fix": list(self.suggested_actions),
        }


def fail(
    code,
    message,
    *,
    operation,
    objects=(),
    status="validation_failed",
    evidence=None,
    fix=None,
):
    raise PhysicsError(
        code="KINCHECK-PHYSICS-" + code,
        message=message,
        operation=operation,
        status=status,
        object_ids=objects,
        details={
            "what_happened": message,
            "cause": code,
            "evidence": plain(evidence or {}),
        },
        suggested_actions=(
            fix or "Correct the named physical input and repeat this operation.",
        ),
    )


def vector(value, name, operation):
    try:
        result = tuple(float(v) for v in value)
        valid = len(result) == 3 and all(math.isfinite(v) for v in result)
    except (ValueError, TypeError):
        valid = False
    if not valid:
        fail(
            "VALUE-INVALID",
            f"{name} must be a finite 3-vector.",
            operation=operation,
            objects=(name,),
        )
    return result


def positive(value, name, operation, *, zero=False):
    if (
        not isinstance(value, (int, float))
        or not math.isfinite(value)
        or (value < 0 if zero else value <= 0)
    ):
        fail(
            "VALUE-INVALID",
            f"{name} must be finite and {'nonnegative' if zero else 'positive'}.",
            operation=operation,
            objects=(name,),
        )


@dataclass(frozen=True, kw_only=True)
class PhysicsMaterial:
    material_id: str
    density: float
    density_unit: str
    source: str
    data_quality: str = "illustrative"

    def __post_init__(self):
        if self.density_unit not in ("kg/m3", "kg/mm3", "kg/m^3", "kg/mm^3"):
            fail(
                "DENSITY-UNIT-INVALID",
                "Density requires kg/m3 or kg/mm3.",
                operation="PhysicsMaterial",
                objects=(self.material_id,),
                evidence={"unit": self.density_unit},
            )
        positive(self.density, "density", "PhysicsMaterial")
        if not self.material_id or not self.source:
            fail(
                "DENSITY-MISSING",
                "Material identity and source are required.",
                operation="PhysicsMaterial",
            )

    @property
    def density_kg_m3(self):
        return self.density * (
            1e9 if self.density_unit in ("kg/mm3", "kg/mm^3") else 1.0
        )


@dataclass(frozen=True, kw_only=True)
class RigidBodyProperties:
    mass_kg: float
    com_m: tuple[float, float, float]
    inertia_com_kg_m2: tuple[tuple[float, float, float], ...]
    frame_id: str
    source_kind: str
    source_ids: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        op = "RigidBodyProperties"
        positive(self.mass_kg, "mass_kg", op)
        object.__setattr__(self, "com_m", vector(self.com_m, "com_m", op))
        try:
            matrix = np.asarray(self.inertia_com_kg_m2, dtype=float)
            valid = matrix.shape == (3, 3) and np.isfinite(matrix).all()
            scale = np.max(np.abs(matrix)) if valid else 0
            valid = valid and np.allclose(
                matrix, matrix.T, rtol=0, atol=max(scale * 1e-10, 1e-20)
            )
            eigen = np.linalg.eigvalsh(matrix) if valid else np.zeros(3)
            valid = (
                valid
                and eigen[0] > 0
                and eigen[2] <= eigen[0] + eigen[1] + max(scale * 1e-10, 1e-20)
            )
        except (ValueError, TypeError):
            valid = False
        if not valid:
            fail(
                "INERTIA-NOT-PHYSICAL",
                "COM inertia must be finite, symmetric, positive definite and obey principal triangle inequalities.",
                operation=op,
                objects=self.source_ids,
                evidence={"unit": "kg*m2"},
            )
        if (
            not self.frame_id
            or not self.source_ids
            or self.source_kind
            not in (
                "brep_integral",
                "measured",
                "mjcf_explicit",
                "mesh_estimate",
                "aggregate",
            )
        ):
            fail(
                "PHYSICS-SOURCE-CONFLICT",
                "An explicit frame, supported source kind and nonempty identity are required.",
                operation=op,
            )
        object.__setattr__(
            self,
            "inertia_com_kg_m2",
            tuple(tuple(float(v) for v in row) for row in matrix),
        )
        object.__setattr__(self, "source_ids", tuple(self.source_ids))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**value)


@dataclass(frozen=True, kw_only=True)
class PhysicsOccurrence:
    occurrence_id: str
    definition_id: str
    revision: str
    content_hash: str
    pose_world: Pose
    properties: RigidBodyProperties
    interfaces: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "interfaces", _freeze_mapping(self.interfaces))


@dataclass(frozen=True, kw_only=True)
class PhysicsManifest:
    definitions: Mapping[str, RigidBodyProperties]
    occurrences: tuple[PhysicsOccurrence, ...]
    source_path: str
    source_sha256: str
    producer: Mapping[str, str]
    schema_version: str = "kincheck.physics/1.0"
    algorithm: str = "occt-volume-com-tensor-si/1"

    def __post_init__(self):
        object.__setattr__(self, "definitions", _freeze_mapping(self.definitions))
        object.__setattr__(self, "producer", _freeze_mapping(self.producer))
        object.__setattr__(self, "occurrences", tuple(self.occurrences))
        ids = [o.occurrence_id for o in self.occurrences]
        if not ids or len(set(ids)) != len(ids):
            fail(
                "OCCURRENCE-COVERAGE-INCOMPLETE",
                "Manifest requires nonempty unique occurrences.",
                operation="PhysicsManifest",
                objects=tuple(ids),
            )

    def to_dict(self):
        payload = plain(self)
        return {**payload, "sha256": digest(payload)}

    @classmethod
    def from_dict(cls, value):
        payload = dict(value)
        expected = payload.pop("sha256", None)
        if (
            expected != digest(payload)
            or payload.get("schema_version") != "kincheck.physics/1.0"
        ):
            fail(
                "PHYSICS-SOURCE-CONFLICT",
                "Manifest schema or hash mismatch.",
                operation="PhysicsManifest.from_dict",
            )
        payload["definitions"] = {
            k: RigidBodyProperties.from_dict(v)
            for k, v in payload["definitions"].items()
        }
        payload["occurrences"] = tuple(
            PhysicsOccurrence(
                **{
                    **o,
                    "pose_world": Pose(**o["pose_world"]),
                    "properties": RigidBodyProperties.from_dict(o["properties"]),
                }
            )
            for o in payload["occurrences"]
        )
        return cls(**payload)


@dataclass(frozen=True, kw_only=True)
class Payload:
    payload_id: str
    component_id: str
    # Existing CAD occurrence = identity-only, never extra mass. Otherwise a
    # measured, component-frame tensor is mandatory for the additional body.
    cad_occurrence_id: str | None = None
    properties: RigidBodyProperties | None = None

    def __post_init__(self):
        if bool(self.cad_occurrence_id) == (self.properties is not None):
            fail(
                "PAYLOAD-DUPLICATED",
                "Choose a CAD payload identity OR additional measured properties.",
                operation="Payload",
                objects=(self.payload_id,),
            )


@dataclass(frozen=True, kw_only=True)
class DynamicsModel:
    assembly: AssemblyModel
    component_properties: Mapping[str, RigidBodyProperties]
    body_properties: Mapping[str, RigidBodyProperties]
    occurrence_components: Mapping[str, str]
    manifest: PhysicsManifest | None = None
    payloads: tuple[Payload, ...] = ()
    base_component_properties: Mapping[str, RigidBodyProperties] = field(
        default_factory=dict
    )

    def __post_init__(self):
        if not self.base_component_properties and not self.payloads:
            # Preserve direct construction of models without additive payloads.
            object.__setattr__(
                self, "base_component_properties", self.component_properties
            )
        for key in (
            "component_properties",
            "body_properties",
            "occurrence_components",
            "base_component_properties",
        ):
            object.__setattr__(self, key, _freeze_mapping(getattr(self, key)))
        object.__setattr__(self, "payloads", tuple(self.payloads))

    @property
    def content_hash(self) -> str:
        """Bind topology, frames, all inertials, payload identities and sources."""
        from .assembly import assembly_to_dict

        def canonical_numbers(value):
            # JSON readers normalize some typed fields (e.g. JointLimit) from
            # int to float. Preserve mathematical identity without rounding
            # fractional values or losing precision in large integer fields.
            if isinstance(value, dict):
                return {k: canonical_numbers(v) for k, v in value.items()}
            if isinstance(value, list):
                return [canonical_numbers(v) for v in value]
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value

        return digest(
            canonical_numbers(
                plain(
                    {
                        "assembly": assembly_to_dict(assembly=self.assembly),
                        "base_component_properties": self.base_component_properties,
                        "component_properties": self.component_properties,
                        "body_properties": self.body_properties,
                        "occurrence_components": self.occurrence_components,
                        "manifest": self.manifest.to_dict() if self.manifest else None,
                        "payloads": self.payloads,
                    }
                )
            )
        )


@dataclass(frozen=True, kw_only=True)
class GravityField:
    acceleration_m_s2: tuple[float, float, float]

    def __post_init__(self):
        object.__setattr__(
            self,
            "acceleration_m_s2",
            vector(self.acceleration_m_s2, "gravity", "GravityField"),
        )


@dataclass(frozen=True, kw_only=True)
class WrenchLoad:
    load_id: str
    component_id: str
    force_n: tuple[float, float, float]
    moment_nm: tuple[float, float, float]
    point_m: tuple[float, float, float]
    frame_id: str
    applied_by: str

    def __post_init__(self):
        for name in ("force_n", "moment_nm", "point_m"):
            object.__setattr__(
                self, name, vector(getattr(self, name), name, "WrenchLoad")
            )
        if not all((self.load_id, self.component_id, self.frame_id, self.applied_by)):
            fail(
                "VALUE-INVALID",
                "Wrench requires load, receiver, expression frame and agent identities.",
                operation="WrenchLoad",
            )


@dataclass(frozen=True, kw_only=True)
class SupportSpec:
    support_id: str
    component_id: str
    occurrence_id: str
    interface_name: str
    kind: str = "fixed"
    frame_id: str = "world"
    point_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    normal: tuple[float, float, float] = (0.0, 0.0, 1.0)
    # Traceable external measurement may be used for an analytical model.
    evidence_source: str | None = None

    def __post_init__(self):
        for name in ("point_m", "normal"):
            object.__setattr__(
                self, name, vector(getattr(self, name), name, "SupportSpec")
            )
        if self.kind not in ("fixed", "unilateral", "frictional"):
            fail(
                "SUPPORT-INVALID",
                "Unsupported support kind.",
                operation="SupportSpec",
                objects=(self.support_id,),
            )
        if (
            not self.interface_name.startswith("interface.")
            or abs(np.linalg.norm(self.normal) - 1) > 1e-9
        ):
            fail(
                "SUPPORT-INVALID",
                "Support requires an interface.* binding and unit normal.",
                operation="SupportSpec",
                objects=(self.support_id,),
            )


@dataclass(frozen=True, kw_only=True)
class StaticRequest:
    gravity: GravityField
    supports: tuple[SupportSpec, ...]
    joint_positions: Mapping[str, float]
    joint_modes: Mapping[str, str]
    loads: tuple[WrenchLoad, ...] = ()
    request_individual_support_reactions: bool = False
    force_tolerance_n: float = 0.01
    moment_tolerance_nm: float = 0.001

    def __post_init__(self):
        for name in ("joint_positions", "joint_modes"):
            object.__setattr__(self, name, _freeze_mapping(getattr(self, name)))
        for name in ("supports", "loads"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for name in ("force_tolerance_n", "moment_tolerance_nm"):
            positive(getattr(self, name), name, "StaticRequest")
        if any(
            mode not in ("free", "locked", "hold") for mode in self.joint_modes.values()
        ):
            fail(
                "STATE-INVALID",
                "Joint mode must be free, locked or hold.",
                operation="StaticRequest",
            )
        if any(not math.isfinite(v) for v in self.joint_positions.values()):
            fail(
                "STATE-INVALID",
                "Static joint coordinates must be finite.",
                operation="StaticRequest",
            )

    @classmethod
    def from_dict(cls, value):
        return cls(
            **{
                **value,
                "gravity": GravityField(**value["gravity"]),
                "supports": tuple(SupportSpec(**s) for s in value["supports"]),
                "loads": tuple(WrenchLoad(**w) for w in value["loads"]),
            }
        )


@dataclass(frozen=True, kw_only=True)
class PhysicsReport(AgentReadableResult):
    operation: str
    status: str = "passed"
    issues: tuple[SimIssue, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)
    model_sha256: str | None = None
    result_index: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "evidence", _freeze_mapping(self.evidence))

    @property
    def passed(self):
        return self.status in (
            "passed",
            "completed",
            "completed_with_warnings",
        ) and not any(i.severity == "error" for i in self.issues)

    def to_dict(self):
        return {
            **plain(self),
            "passed": self.passed,
            "what_happened": "Requested claim established."
            if self.passed
            else "; ".join(i.message for i in self.issues),
            "cause": "All requested checks passed."
            if self.passed
            else "; ".join(i.code for i in self.issues),
            "how_to_fix": []
            if self.passed
            else [a for i in self.issues for a in i.suggested_actions],
        }


@dataclass(frozen=True, kw_only=True)
class StaticResult(PhysicsReport):
    operation: str = "solve_static_equilibrium"
    model_sha256: str | None = None
    request: StaticRequest | None = None
    generalized_holding: Mapping[str, float] = field(default_factory=dict)
    generalized_units: Mapping[str, str] = field(default_factory=dict)
    support_wrench: Mapping[str, Any] = field(default_factory=dict)
    joint_reactions: Mapping[str, Any] = field(default_factory=dict)
    body_residuals: Mapping[str, Any] = field(default_factory=dict)
    component_poses: Mapping[str, Pose] = field(default_factory=dict)
    load_wrenches: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self):
        super().__post_init__()
        op = "StaticResult"
        if set(self.generalized_holding) != set(self.generalized_units):
            fail(
                "RESULT-INVALID",
                "Holding values and units must cover the same joints.",
                operation=op,
            )
        for jid, value in self.generalized_holding.items():
            if (
                not isinstance(value, (int, float))
                or not math.isfinite(value)
                or self.generalized_units[jid] not in ("N", "N*m")
            ):
                fail(
                    "RESULT-INVALID",
                    "Holding effort must be finite and use N or N*m.",
                    operation=op,
                    objects=(jid,),
                )
        for record in (
            *self.body_residuals.values(),
            *self.joint_reactions.values(),
            *self.load_wrenches,
        ):
            for key in ("force_n", "moment_nm"):
                vector(record.get(key, ()), key, op)
        if self.status in ("passed", "completed", "completed_with_warnings") and (
            not self.body_residuals
            or not self.component_poses
            or not self.support_wrench
        ):
            fail(
                "RESULT-INCOMPLETE",
                "Completed statics requires body balance, poses and support evidence.",
                operation=op,
            )
        if self.support_wrench:
            for key in ("force_n", "moment_nm", "reference_point_m"):
                vector(self.support_wrench.get(key, ()), key, op)
        for name in (
            "generalized_holding",
            "generalized_units",
            "support_wrench",
            "joint_reactions",
            "body_residuals",
            "component_poses",
        ):
            object.__setattr__(self, name, _freeze_mapping(getattr(self, name)))
        object.__setattr__(
            self, "load_wrenches", tuple(_freeze_mapping(v) for v in self.load_wrenches)
        )

    @classmethod
    def from_dict(cls, value):
        payload = {f.name: value[f.name] for f in fields(cls) if f.name in value}
        if payload.get("request") is not None:
            payload["request"] = StaticRequest.from_dict(payload["request"])
        payload["issues"] = tuple(
            SimIssue(**{**i, "evidence": tuple(Evidence(**e) for e in i["evidence"])})
            for i in payload.get("issues", ())
        )
        payload["component_poses"] = {
            k: Pose(**v) for k, v in payload.get("component_poses", {}).items()
        }
        return cls(**payload)


def issue(
    code,
    message,
    operation,
    objects=(),
    *,
    actual=None,
    expected=None,
    unit=None,
    fix=None,
):
    return SimIssue(
        code="KINCHECK-PHYSICS-" + code,
        severity="error",
        stage=operation,
        message=message,
        object_ids=tuple(objects),
        evidence=(Evidence(key=code, actual=actual, expected=expected, unit=unit),),
        suggested_actions=(
            fix or "Correct the named input or request a supported physical claim.",
        ),
    )
