"""Kinematic verification implemented by the first KinCheckAPI milestone."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
import statistics
from typing import Any, Literal, Mapping, NoReturn, Sequence

from .assembly import (
    AssemblyModel,
    Joint,
    Pose,
    build_kinematic_tree,
    validate_assembly,
    validate_topology,
)
from .diagnostics import AgentReadableResult, BackendFailure, DiagnosticReport, Evidence, SimIssue
from .errors import (
    BackendCapabilityError,
    BackendUnavailableError,
    AssemblyValidationError,
    KinCheckError,
    MotionSolveError,
    ScenarioValidationError,
)
from .result import (
    ConstraintEquationResidual,
    ConstraintResidual,
    Direction,
    JointTrajectory,
    MotionResult,
    IntegrationSample,
    DriverTarget,
    DriverTrajectory,
    _PlanetaryStageEvidence,
    Trajectory,
    TransmissionRatioCheck,
)
from .pose import compose_pose, orientation_error_rad, relative_pose, rotate_vector
from .scenario import Scenario, validate_scenario, PositionDriver, SpeedDriver
from .kinematics_geometry import (
    JacobianOptions,
    JacobianResult,
    MobilityReport,
    PoseTarget,
    PositionSolveOptions,
    analyze_mobility,
    compute_jacobian,
    solve_position_core,
)
from .kinematics_analysis import (
    ConnectorPathResult,
    ReachabilityOptions,
    SingularityOptions,
    SingularitySample,
    TargetReference,
    WorkspaceOptions,
    WorkspaceResult,
    WorkspaceSample,
)
from .kinematics_limits import detect_limit_events


Member = Literal["sun", "ring", "carrier"]


@dataclass(frozen=True, slots=True, kw_only=True)
class KinematicSolveOptions:
    """Deterministic controls for backend integration and constraint solving."""
    max_integration_step_s: float | None = None
    max_integration_substeps: int = 1000000
    max_constraint_iterations: int = 100
    position_residual_tolerance_m: float = 1e-6
    orientation_residual_tolerance_rad: float = 1e-6
    non_finite_state_policy: Literal["fail", "warn"] = "fail"
    adaptive_sampling: bool = False

    def __post_init__(self) -> None:
        if self.max_integration_step_s is not None and (not math.isfinite(float(self.max_integration_step_s)) or float(self.max_integration_step_s) <= 0):
            raise ValueError("max_integration_step_s must be positive and finite")
        if int(self.max_integration_substeps) <= 0 or int(self.max_constraint_iterations) <= 0:
            raise ValueError("solver iteration limits must be positive")
        if not math.isfinite(float(self.position_residual_tolerance_m)) or float(self.position_residual_tolerance_m) < 0:
            raise ValueError("position_residual_tolerance_m must be finite and non-negative")
        if not math.isfinite(float(self.orientation_residual_tolerance_rad)) or float(self.orientation_residual_tolerance_rad) < 0:
            raise ValueError("orientation_residual_tolerance_rad must be finite and non-negative")
        if self.non_finite_state_policy not in {"fail", "warn"}:
            raise ValueError("non_finite_state_policy must be 'fail' or 'warn'")
        if not isinstance(self.adaptive_sampling, bool):
            raise TypeError("adaptive_sampling must be a boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_integration_step_s": self.max_integration_step_s,
            "max_integration_substeps": int(self.max_integration_substeps),
            "max_constraint_iterations": int(self.max_constraint_iterations),
            "position_residual_tolerance_m": float(self.position_residual_tolerance_m),
            "orientation_residual_tolerance_rad": float(self.orientation_residual_tolerance_rad),
            "non_finite_state_policy": self.non_finite_state_policy,
            "adaptive_sampling": self.adaptive_sampling,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class KinematicCapabilities:
    joint_types: Mapping[str, bool]
    driver_modes: tuple[str, ...] = ("position", "speed")
    output_channels: tuple[str, ...] = ("joint", "component", "connector", "residuals")
    analysis_capabilities: Mapping[str, bool] = field(default_factory=lambda: {
        "path_tracking": True,
        "planar_tracking": True,
        "periodic_motion": True,
        "start_stop_reversal": True,
        "synchronization": True,
        "pose_trajectory_driver": False,
        "general_inverse_kinematics": False,
        "continuous_time_of_impact": False,
    })

    def to_dict(self) -> dict[str, Any]:
        return {
            "joint_types": dict(self.joint_types),
            "driver_modes": list(self.driver_modes),
            "output_channels": list(self.output_channels),
            "analysis_capabilities": dict(self.analysis_capabilities),
        }


def backend_capabilities() -> KinematicCapabilities:
    return KinematicCapabilities(joint_types={"fixed": True, "revolute": True, "prismatic": True, "cylindrical": False, "spherical": False, "planar": False, "free": False})


@dataclass(frozen=True, slots=True, kw_only=True)
class DofReport(AgentReadableResult):
    total_dofs: int
    joint_dofs: Mapping[str, int]
    component_dofs: Mapping[str, int]
    issues: tuple[SimIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "analyze_dofs",
            "status": "passed" if self.passed else "failed",
            "total_dofs": self.total_dofs,
            "joint_dofs": dict(self.joint_dofs),
            "component_dofs": dict(self.component_dofs),
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ClosureReport(AgentReadableResult):
    passed: bool
    residuals: tuple[Any, ...] = ()
    issues: tuple[SimIssue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "validate_closures",
            "status": "passed" if self.passed else "failed",
            "residuals": [
                item.to_dict() if hasattr(item, "to_dict") else item for item in self.residuals
            ],
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class PositionResult(AgentReadableResult):
    passed: bool
    joint_positions: Mapping[str, float]
    component_poses: Mapping[str, Any]
    residuals: tuple[Any, ...] = ()
    issues: tuple[SimIssue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "passed": self.passed,
            "operation": "solve_position",
            "status": "passed" if self.passed else "failed",
            "joint_positions": dict(self.joint_positions),
            "component_poses": {
                key: value.to_dict() if hasattr(value, "to_dict") else value
                for key, value in self.component_poses.items()
            },
            "residuals": [
                item.to_dict() if hasattr(item, "to_dict") else item for item in self.residuals
            ],
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ReachabilityResult(AgentReadableResult):
    reachable: bool
    target: Any
    position_result: PositionResult | None = None
    issues: tuple[SimIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.reachable and not any(
            issue.severity == "error" for issue in self.issues
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "reachable": self.reachable,
            "passed": self.passed,
            "operation": "check_reachability",
            "status": "passed" if self.passed else "failed",
            "target": self.target.to_dict() if hasattr(self.target, "to_dict") else self.target,
            "position_result": (
                self.position_result.to_dict() if self.position_result is not None else None
            ),
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class SingularityReport(AgentReadableResult):
    singular_times_s: tuple[float, ...]
    tolerance: float
    issues: tuple[SimIssue, ...] = ()
    samples: tuple[Any, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.singular_times_s and not any(
            issue.severity == "error" for issue in self.issues
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "passed": self.passed,
            "operation": "find_singularities",
            "status": "passed" if self.passed else "failed",
            "singular_times_s": list(self.singular_times_s),
            "tolerance": self.tolerance,
            "samples": [item.to_dict() if hasattr(item, "to_dict") else item for item in self.samples],
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class SolveAttempt(AgentReadableResult):
    """Structured outcome returned by :func:`try_solve_motion`."""

    status: Literal[
        "completed",
        "completed_with_warnings",
        "partial",
        "validation_failed",
        "capability_failed",
        "failed",
    ]
    succeeded: bool
    motion_result: MotionResult | None
    last_valid_result: MotionResult | None
    report: DiagnosticReport
    failure: KinCheckError | None

    def __post_init__(self) -> None:
        expected_success = self.status in {
            "completed",
            "completed_with_warnings",
        }
        if self.succeeded != expected_success:
            raise ValueError("SolveAttempt.succeeded does not match status")
        if self.succeeded and (self.motion_result is None or self.failure is not None):
            raise ValueError("A successful SolveAttempt requires a result and no failure")
        if self.status == "partial":
            if (
                self.motion_result is not None
                or self.last_valid_result is None
                or self.last_valid_result.status != "partial"
                or self.failure is not None
            ):
                raise ValueError("A partial SolveAttempt keeps only last_valid_result")
        elif not self.succeeded and (self.motion_result is not None or self.failure is None):
            raise ValueError("A failed SolveAttempt requires failure and no complete result")
        elif self.succeeded and self.motion_result is not None and self.motion_result.status != self.status:
            raise ValueError("A successful SolveAttempt status must match its MotionResult")

    @property
    def passed(self) -> bool:
        return self.succeeded

    @property
    def issues(self) -> tuple[SimIssue, ...]:
        return self.report.issues

    @property
    def operation(self) -> str:
        return "try_solve_motion"

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "operation": self.operation,
            "status": self.status,
            "passed": self.passed,
            "succeeded": self.succeeded,
            "motion_result": (
                self.motion_result.to_dict() if self.motion_result is not None else None
            ),
            "last_valid_result": (
                self.last_valid_result.to_dict()
                if self.last_valid_result is not None
                else None
            ),
            "report": self.report.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "failure": self.failure.to_dict() if self.failure is not None else None,
        }


def _issue(
    *, code: str, message: str, object_ids: Sequence[str], evidence: Sequence[Evidence], action: str
) -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage="kinematics.ratio",
        message=message,
        object_ids=tuple(object_ids),
        evidence=tuple(evidence),
        suggested_actions=(action,),
    )


def _normalize_joint_ids(value: str | Sequence[str], *, name: str) -> tuple[str, ...]:
    values = (value,) if isinstance(value, str) else tuple(value)
    if not values or any(not isinstance(item, str) or not item for item in values):
        raise TypeError(f"{name} must contain one or more explicit Joint IDs")
    return values


def _stage_parameters(*, assembly: AssemblyModel) -> tuple[Mapping[str, Any], ...]:
    parameters = assembly.metadata.get("design_parameters", {})
    if not isinstance(parameters, Mapping):
        return ()
    count = int(parameters.get("stage_count", 0))
    common = {
        "sun_teeth": parameters.get("sun_teeth"),
        "planet_teeth": parameters.get("planet_teeth"),
        "ring_teeth": parameters.get("ring_teeth"),
    }
    stages: list[Mapping[str, Any]] = []
    for index in range(1, count + 1):
        specific = parameters.get(f"stage_{index}")
        if isinstance(specific, Mapping):
            stages.append(specific)
        elif all(value is not None for value in common.values()):
            stages.append(common)
    return tuple(stages)


def _component_is_grounded(*, assembly: AssemblyModel, component_id: str) -> bool:
    return any(item.component_id == component_id for item in assembly.grounds)


def _joint_member_component(
    *, assembly: AssemblyModel, joint: Joint, member: Member
) -> str:
    candidates = (joint.connector_a.component_id, joint.connector_b.component_id)
    if member == "ring":
        return next(
            (item for item in candidates if _component_is_grounded(assembly=assembly, component_id=item)),
            candidates[1],
        )
    return next(
        (item for item in reversed(candidates) if not _component_is_grounded(assembly=assembly, component_id=item)),
        candidates[1],
    )


def _verify_planetary_ratio_definition_v012(
    *,
    assembly: AssemblyModel,
    sun_joint_id: str | Sequence[str],
    ring_joint_id: str | Sequence[str],
    carrier_joint_id: str | Sequence[str],
    fixed_member: Member,
    input_member: Member,
    output_member: Member,
    expected_ratio: float,
    expected_direction: Direction = "same",
    relative_tolerance: float = 1e-9,
) -> TransmissionRatioCheck:
    """Validate explicit fixed-ring planetary definitions without time simulation.

    Each Joint ID sequence is ordered by stage. A scalar ID is accepted for a
    single stage. The first milestone deliberately supports the fixed-ring,
    sun-input, carrier-output configuration used by ex1 and ex2.
    """

    sun_ids = _normalize_joint_ids(sun_joint_id, name="sun_joint_id")
    ring_ids = _normalize_joint_ids(ring_joint_id, name="ring_joint_id")
    carrier_ids = _normalize_joint_ids(carrier_joint_id, name="carrier_joint_id")
    all_ids = (*sun_ids, *ring_ids, *carrier_ids)
    issues: list[SimIssue] = []
    evidence: list[Evidence] = []
    stages = _stage_parameters(assembly=assembly)

    if not math.isfinite(expected_ratio) or expected_ratio <= 0.0:
        issues.append(
            _issue(
                code="KINCHECK-RATIO-EXPECTED-INVALID",
                message="Expected transmission ratio must be finite and positive.",
                object_ids=(assembly.assembly_id,),
                evidence=(Evidence(key="expected_ratio", actual=expected_ratio, expected="> 0"),),
                action="Provide a positive input-speed/output-speed magnitude ratio.",
            )
        )
    if not math.isfinite(relative_tolerance) or relative_tolerance < 0.0:
        issues.append(
            _issue(
                code="KINCHECK-RATIO-TOLERANCE-INVALID",
                message="Relative tolerance must be finite and non-negative.",
                object_ids=(assembly.assembly_id,),
                evidence=(Evidence(key="relative_tolerance", actual=relative_tolerance, expected=">= 0"),),
                action="Provide a finite non-negative relative tolerance.",
            )
        )
    if expected_direction not in {"same", "opposite"}:
        issues.append(
            _issue(
                code="KINCHECK-RATIO-DIRECTION-INVALID",
                message="Expected direction must be 'same' or 'opposite'.",
                object_ids=(assembly.assembly_id,),
                evidence=(Evidence(key="expected_direction", actual=expected_direction),),
                action="Use expected_direction='same' or 'opposite'.",
            )
        )

    roles = (fixed_member, input_member, output_member)
    if roles != ("ring", "sun", "carrier"):
        issues.append(
            _issue(
                code="KINCHECK-RATIO-CONFIGURATION-UNSUPPORTED",
                message="This milestone verifies only fixed-ring, sun-input, carrier-output planetary stages.",
                object_ids=(assembly.assembly_id,),
                evidence=(Evidence(key="roles", actual=roles, expected=("ring", "sun", "carrier")),),
                action="Use explicit fixed_member='ring', input_member='sun', output_member='carrier'.",
            )
        )
    if not (len(sun_ids) == len(ring_ids) == len(carrier_ids) == len(stages)):
        issues.append(
            _issue(
                code="KINCHECK-RATIO-STAGE-COUNT-MISMATCH",
                message="Joint ID sequences and explicit design stages must have the same length.",
                object_ids=(assembly.assembly_id, *all_ids),
                evidence=(
                    Evidence(
                        key="stage_counts",
                        actual={
                            "sun": len(sun_ids),
                            "ring": len(ring_ids),
                            "carrier": len(carrier_ids),
                            "design": len(stages),
                        },
                    ),
                ),
                action="Provide one explicit sun, ring, and carrier Joint ID per design stage.",
            )
        )

    joints: dict[str, Joint] = {}
    role_by_id: dict[str, set[Member]] = {}
    for role, role_ids in (("sun", sun_ids), ("ring", ring_ids), ("carrier", carrier_ids)):
        for joint_id in role_ids:
            role_by_id.setdefault(joint_id, set()).add(role)
    for index, (sun_id, carrier_id) in enumerate(zip(sun_ids, carrier_ids), start=1):
        if sun_id == carrier_id:
            issues.append(
                _issue(
                    code="KINCHECK-RATIO-ROLE-JOINT-CONFLICT",
                    message="Sun and carrier roles must use distinct explicit Joint IDs within a stage.",
                    object_ids=(assembly.assembly_id, f"stage_{index}", sun_id),
                    evidence=(Evidence(key="joint_id", actual=sun_id),),
                    action="Reference the separate sun and carrier revolute relations.",
                )
            )
    for joint_id in dict.fromkeys(all_ids):
        joint = assembly.get_joint(joint_id=joint_id)
        if joint is None:
            issues.append(
                _issue(
                    code="KINCHECK-RATIO-JOINT-NOT-FOUND",
                    message="Planetary verification references an unknown Joint ID.",
                    object_ids=(assembly.assembly_id, joint_id),
                    evidence=(Evidence(key="joint_id", actual=joint_id),),
                    action="Use a revolute Joint ID present in the converted Assembly.",
                )
            )
        elif joint.joint_type.value != "revolute" and not (
            joint.joint_type.value == "fixed" and "ring" in role_by_id[joint_id]
        ):
            issues.append(
                _issue(
                    code="KINCHECK-RATIO-JOINT-TYPE-INVALID",
                    message="Sun, ring, and carrier roles must reference revolute joints.",
                    object_ids=(joint_id,),
                    evidence=(Evidence(key="joint_type", actual=joint.joint_type.value, expected="revolute"),),
                    action="Reference the explicit revolute relation for this member.",
                )
            )
        else:
            joints[joint_id] = joint

    stage_checks: list[_PlanetaryStageEvidence] = []
    measured_total: float | None = 1.0
    usable_count = min(len(stages), len(sun_ids), len(ring_ids), len(carrier_ids))
    for index in range(usable_count):
        raw = stages[index]
        try:
            sun_teeth = int(raw["sun_teeth"])
            planet_teeth = int(raw["planet_teeth"])
            ring_teeth = int(raw["ring_teeth"])
        except (KeyError, TypeError, ValueError):
            sun_teeth = planet_teeth = ring_teeth = 0
        stage_id = f"stage_{index + 1}"
        stage_ratio: float | None = None
        if sun_teeth <= 0 or planet_teeth <= 0 or ring_teeth <= 0:
            issues.append(
                _issue(
                    code="KINCHECK-RATIO-TEETH-INVALID",
                    message="Every stage requires positive explicit sun, planet, and ring tooth counts.",
                    object_ids=(assembly.assembly_id, stage_id),
                    evidence=(Evidence(key="teeth", actual=dict(raw)),),
                    action="Correct the stage design_parameters tooth counts.",
                )
            )
            measured_total = None
        elif ring_teeth != sun_teeth + 2 * planet_teeth:
            issues.append(
                _issue(
                    code="KINCHECK-RATIO-TOOTH-RELATION-INVALID",
                    message="Coaxial planetary tooth counts do not satisfy R = S + 2P.",
                    object_ids=(assembly.assembly_id, stage_id),
                    evidence=(
                        Evidence(key="ring_teeth", actual=ring_teeth, expected=sun_teeth + 2 * planet_teeth),
                    ),
                    action="Correct the tooth counts or the declared planetary topology.",
                )
            )
            measured_total = None
        else:
            stage_ratio = 1.0 + ring_teeth / sun_teeth
            if measured_total is not None:
                measured_total *= stage_ratio

        declared_ratios = assembly.metadata.get("ratio", {})
        declared_stage_ratio = None
        if isinstance(declared_ratios, Mapping):
            declared_stage_ratio = declared_ratios.get(
                f"stage_{index + 1}_ratio", declared_ratios.get("stage_ratio")
            )
        if stage_ratio is not None and declared_stage_ratio is not None:
            declared_error = abs(stage_ratio - float(declared_stage_ratio)) / stage_ratio
            if declared_error > relative_tolerance:
                issues.append(
                    _issue(
                        code="KINCHECK-RATIO-STAGE-MISMATCH",
                        message="Calculated stage ratio differs from the imported source's declared stage ratio.",
                        object_ids=(assembly.assembly_id, stage_id),
                        evidence=(
                            Evidence(key="calculated_ratio", actual=stage_ratio, expected=float(declared_stage_ratio)),
                        ),
                        action="Correct the declared stage ratio or the explicit tooth counts.",
                    )
                )
        ring_joint = joints.get(ring_ids[index])
        if ring_joint is not None:
            ring_component = _joint_member_component(
                assembly=assembly, joint=ring_joint, member="ring"
            )
            if not _component_is_grounded(assembly=assembly, component_id=ring_component):
                issues.append(
                    _issue(
                        code="KINCHECK-RATIO-FIXED-MEMBER-NOT-GROUNDED",
                        message="The explicit ring member is not grounded in this Assembly.",
                        object_ids=(ring_ids[index], ring_component),
                        evidence=(Evidence(key="fixed_member", actual=ring_component, expected="grounded"),),
                        action="Ground the ring component or correct ring_joint_id.",
                    )
                )
        stage_checks.append(
            _PlanetaryStageEvidence(
                stage_id=stage_id,
                sun_teeth=sun_teeth,
                planet_teeth=planet_teeth,
                ring_teeth=ring_teeth,
                measured_ratio=stage_ratio,
                expected_ratio=(
                    float(declared_stage_ratio)
                    if declared_stage_ratio is not None
                    else stage_ratio
                ),
                relative_error=(
                    abs(stage_ratio - float(declared_stage_ratio)) / float(declared_stage_ratio)
                    if stage_ratio is not None
                    and declared_stage_ratio is not None
                    and float(declared_stage_ratio) != 0.0
                    else (0.0 if stage_ratio is not None else None)
                ),
            )
        )

    relative_error = (
        abs(measured_total - expected_ratio) / expected_ratio
        if measured_total is not None and math.isfinite(expected_ratio) and expected_ratio > 0.0
        else None
    )
    if relative_error is not None and relative_error > relative_tolerance:
        issues.append(
            _issue(
                code="KINCHECK-RATIO-MISMATCH",
                message="Calculated total planetary ratio differs from the expected ratio.",
                object_ids=(assembly.assembly_id, *all_ids),
                evidence=(
                    Evidence(key="measured_ratio", actual=measured_total, expected=expected_ratio),
                    Evidence(key="relative_error", actual=relative_error, expected=f"<= {relative_tolerance}"),
                ),
                action="Correct the expected ratio, tooth counts, or member roles.",
            )
        )
    measured_direction: Direction = "same"
    if expected_direction != measured_direction:
        issues.append(
            _issue(
                code="KINCHECK-RATIO-DIRECTION-MISMATCH",
                message="Fixed-ring sun-input carrier-output stages rotate in the same direction.",
                object_ids=(assembly.assembly_id,),
                evidence=(Evidence(key="direction", actual=measured_direction, expected=expected_direction),),
                action="Correct expected_direction or the explicit member configuration.",
            )
        )
    evidence.extend(
        (
            Evidence(key="stage_count", actual=usable_count, expected=len(stages)),
            Evidence(key="total_ratio", actual=measured_total, expected=expected_ratio),
            Evidence(key="ratio_definition", actual="abs(input_speed/output_speed)"),
        )
    )
    return TransmissionRatioCheck(
        passed=not issues,
        expected_ratio=expected_ratio,
        measured_ratio=measured_total,
        relative_error=relative_error,
        expected_direction=expected_direction,
        measured_direction=measured_direction,
        input_joint_id=sun_ids[0],
        output_joint_id=carrier_ids[-1],
        input_member=input_member,
        output_member=output_member,
        fixed_member=fixed_member,
        stage_checks=tuple(stage_checks),
        evidence=tuple(evidence),
        issues=tuple(issues),
    )


def _measurement_issue(
    *, code: str, message: str, object_ids: Sequence[str], evidence: Sequence[Evidence] = ()
) -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage="kinematics.ratio.measurement",
        message=message,
        object_ids=tuple(object_ids),
        evidence=tuple(evidence),
        suggested_actions=("Inspect the requested trajectories and measurement settings.",),
    )


def _verify_transmission_ratio_v012(
    *,
    motion_result: Any,
    input_joint_id: str,
    output_joint_id: str,
    expected_ratio: float,
    expected_direction: Direction,
    measurement: str = "angular_velocity",
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    relative_tolerance: float = 1e-3,
    minimum_input_magnitude: float = 1e-6,
) -> TransmissionRatioCheck:
    """Measure a transmission ratio from backend-independent motion samples."""

    issues: list[SimIssue] = []
    if measurement not in {"angular_position", "angular_velocity", "angular_acceleration"}:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-MEASUREMENT-UNSUPPORTED",
                message="Unsupported ratio measurement quantity.",
                object_ids=(input_joint_id, output_joint_id),
                evidence=(Evidence(key="measurement", actual=measurement),),
            )
        )
    if not math.isfinite(expected_ratio) or expected_ratio <= 0.0:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-EXPECTED-INVALID",
                message="Expected ratio must be finite and positive.",
                object_ids=(input_joint_id, output_joint_id),
                evidence=(Evidence(key="expected_ratio", actual=expected_ratio, expected="> 0"),),
            )
        )
    if expected_direction not in {"same", "opposite"}:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-DIRECTION-INVALID",
                message="Expected direction must be 'same' or 'opposite'.",
                object_ids=(input_joint_id, output_joint_id),
            )
        )
    if not math.isfinite(relative_tolerance) or relative_tolerance < 0.0:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-TOLERANCE-INVALID",
                message="Relative tolerance must be finite and non-negative.",
                object_ids=(input_joint_id, output_joint_id),
            )
        )
    if not math.isfinite(minimum_input_magnitude) or minimum_input_magnitude < 0.0:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-MINIMUM-INPUT-INVALID",
                message="Minimum input magnitude must be finite and non-negative.",
                object_ids=(input_joint_id,),
            )
        )

    trajectories = getattr(motion_result, "joint_trajectories", {})
    input_trajectory = trajectories.get(input_joint_id) if hasattr(trajectories, "get") else None
    output_trajectory = trajectories.get(output_joint_id) if hasattr(trajectories, "get") else None
    if input_trajectory is None or output_trajectory is None:
        missing = tuple(
            joint_id
            for joint_id, trajectory in (
                (input_joint_id, input_trajectory),
                (output_joint_id, output_trajectory),
            )
            if trajectory is None
        )
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-TRAJECTORY-NOT-FOUND",
                message="Motion result lacks one or more requested Joint trajectories.",
                object_ids=missing,
            )
        )

    attribute = {
        "angular_position": "position_rad_or_m",
        "angular_velocity": "velocity_rad_s_or_m_s",
        "angular_acceleration": "acceleration_rad_s2_or_m_s2",
    }.get(measurement)
    ratios: list[float] = []
    directions: list[Direction] = []
    rejected = 0
    if input_trajectory is not None and output_trajectory is not None and attribute:
        outputs = {sample.time_s: sample for sample in output_trajectory.samples}
        for input_sample in input_trajectory.samples:
            if start_time_s is not None and input_sample.time_s < start_time_s:
                continue
            if end_time_s is not None and input_sample.time_s > end_time_s:
                continue
            output_sample = outputs.get(input_sample.time_s)
            if output_sample is None:
                rejected += 1
                continue
            input_value = float(getattr(input_sample, attribute))
            output_value = float(getattr(output_sample, attribute))
            if abs(input_value) < minimum_input_magnitude or abs(output_value) < 1e-15:
                rejected += 1
                continue
            ratios.append(abs(input_value / output_value))
            directions.append("same" if input_value * output_value >= 0.0 else "opposite")

    measured_ratio = statistics.median(ratios) if ratios else None
    measured_direction: Direction | None = None
    if directions:
        measured_direction = max(("same", "opposite"), key=directions.count)  # type: ignore[assignment]
    relative_error = (
        abs(measured_ratio - expected_ratio) / expected_ratio
        if measured_ratio is not None and math.isfinite(expected_ratio) and expected_ratio > 0.0
        else None
    )
    if not ratios:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-INSUFFICIENT-SAMPLES",
                message="No valid samples remain in the requested measurement interval.",
                object_ids=(input_joint_id, output_joint_id),
                evidence=(Evidence(key="rejected_sample_count", actual=rejected),),
            )
        )
    elif relative_error is not None and relative_error > relative_tolerance:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-MISMATCH",
                message="Measured transmission ratio differs from the expected ratio.",
                object_ids=(input_joint_id, output_joint_id),
                evidence=(
                    Evidence(key="measured_ratio", actual=measured_ratio, expected=expected_ratio),
                    Evidence(key="relative_error", actual=relative_error, expected=f"<= {relative_tolerance}"),
                ),
            )
        )
    if measured_direction is not None and measured_direction != expected_direction:
        issues.append(
            _measurement_issue(
                code="KINCHECK-RATIO-DIRECTION-MISMATCH",
                message="Measured input and output directions differ from the expectation.",
                object_ids=(input_joint_id, output_joint_id),
                evidence=(Evidence(key="direction", actual=measured_direction, expected=expected_direction),),
            )
        )
    return TransmissionRatioCheck(
        passed=not issues,
        expected_ratio=expected_ratio,
        measured_ratio=measured_ratio,
        relative_error=relative_error,
        expected_direction=expected_direction,
        measured_direction=measured_direction,
        input_joint_id=input_joint_id,
        output_joint_id=output_joint_id,
        sample_count=len(ratios),
        rejected_sample_count=rejected,
        start_time_s=start_time_s,
        end_time_s=end_time_s,
        evidence=(Evidence(key="measurement", actual=measurement),),
        issues=tuple(issues),
    )


def verify_transmission_ratio(*, motion_result: MotionResult, input_joint_id: str, output_joint_id: str, expected_ratio: float, expected_direction: Direction, measurement: str = "angular_velocity", start_time_s: float | None = None, end_time_s: float | None = None, relative_tolerance: float = 1e-3, minimum_sample_count: int = 3, minimum_valid_fraction: float = 0.8, minimum_input_magnitude: float = 1e-9, minimum_output_magnitude: float = 1e-12, check_id: str = "transmission_ratio") -> Any:
    """Deprecated compatibility wrapper for :mod:`kincheckapi.checks`."""

    import warnings

    warnings.warn(
        "kincheckapi.kinematics.verify_transmission_ratio() is deprecated; "
        "use kincheckapi.checks.check_transmission_ratio().",
        DeprecationWarning,
        stacklevel=2,
    )
    from .checks import check_transmission_ratio

    return check_transmission_ratio(motion_result=motion_result, input_joint_id=input_joint_id, output_joint_id=output_joint_id, expected_ratio=expected_ratio, expected_direction=expected_direction, measurement=measurement, start_time_s=start_time_s, end_time_s=end_time_s, relative_tolerance=relative_tolerance, minimum_sample_count=minimum_sample_count, minimum_valid_fraction=minimum_valid_fraction, minimum_input_magnitude=minimum_input_magnitude, minimum_output_magnitude=minimum_output_magnitude, check_id=check_id)


def analyze_dofs(*, assembly: AssemblyModel) -> DofReport:
    dofs_by_type = {
        "fixed": 0,
        "revolute": 1,
        "prismatic": 1,
        "cylindrical": 2,
        "spherical": 3,
        "planar": 3,
        "free": 6,
    }
    joint_dofs = {
        joint.joint_id: dofs_by_type[joint.joint_type.value] for joint in assembly.joints
    }
    grounded = {item.component_id for item in assembly.grounds}
    component_dofs = {
        component.component_id: (
            0
            if component.component_id in grounded
            else sum(
                joint_dofs[joint.joint_id]
                for joint in assembly.joints
                if component.component_id
                in {joint.connector_a.component_id, joint.connector_b.component_id}
            )
        )
        for component in assembly.components
    }
    return DofReport(
        total_dofs=sum(joint_dofs.values()),
        joint_dofs=joint_dofs,
        component_dofs=component_dofs,
    )


def validate_closures(
    *, assembly: AssemblyModel | None = None, motion_result: MotionResult | None = None, **_: Any
) -> ClosureReport | None:
    """Validate authored or solved Closure residuals.

    Calling the compatibility shim without an assembly or result continues to
    return ``None``.  With an assembly, the authored component poses are checked
    before a solver is started; with a MotionResult, the recorded samples and
    declared Closure tolerances are checked.
    """

    if assembly is None and motion_result is None:
        return None
    if motion_result is not None:
        closure_ids = {item.constraint_id for item in motion_result.closure_residuals}
        residuals = tuple(item for item in motion_result.closure_residuals if item.constraint_id in closure_ids)
        issues = tuple(
            issue for issue in motion_result.issues if "CLOSURE" in issue.code
        )
        if motion_result.status == "partial":
            issues = (
                *issues,
                SimIssue(
                    code="KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE",
                    severity="error",
                    stage="kinematics.closure",
                    message="A partial MotionResult cannot complete closure validation.",
                    object_ids=(motion_result.scenario_id, motion_result.assembly_id),
                    evidence=(
                        Evidence(key="motion_result_status", actual=motion_result.status, expected="completed or completed_with_warnings"),
                        Evidence(key="sample_count", actual=len(motion_result.sample_times_s)),
                        Evidence(key="time_range_s", actual=(motion_result.start_time_s, motion_result.end_time_s), unit="s"),
                    ),
                    failure_time_s=motion_result.end_time_s,
                ),
            )
        return ClosureReport(
            passed=not issues and all(
                status == "passed" for status in motion_result.closure_statuses.values()
            ),
            residuals=residuals,
            issues=issues,
        )
    assert assembly is not None
    topology = build_kinematic_tree(assembly=assembly)
    topology_issues = tuple(
        issue for issue in validate_topology(assembly=assembly).issues
        if issue.code.startswith("topology.")
    )
    residuals: list[ConstraintResidual] = []
    closure_issues: list[SimIssue] = list(topology_issues)
    for closure in assembly.closures:
        a = assembly.get_component(component_id=closure.constraint.connector_a.component_id)
        b = assembly.get_component(component_id=closure.constraint.connector_b.component_id)
        connector_a = assembly.get_connector(
            component_id=closure.constraint.connector_a.component_id,
            connector_id=closure.constraint.connector_a.connector_id,
        )
        connector_b = assembly.get_connector(
            component_id=closure.constraint.connector_b.component_id,
            connector_id=closure.constraint.connector_b.connector_id,
        )
        if a is None or b is None or connector_a is None or connector_b is None:
            closure_issues.append(
                SimIssue(
                    code="KINCHECK-CLOSURE-ENDPOINT-MISSING",
                    severity="error",
                    stage="kinematics.closure",
                    message="A Closure endpoint could not be resolved.",
                    object_ids=(closure.closure_id,),
                    suggested_actions=("Export both Closure Connector endpoints.",),
                )
            )
            continue
        pose_a = compose_pose(parent=a.initial_pose, child=connector_a.pose)
        pose_b = compose_pose(parent=b.initial_pose, child=connector_b.pose)
        position = math.dist(pose_a.position_m, pose_b.position_m)
        orientation = (
            _axis_alignment_error(pose_a, pose_b)
            if closure.constraint.metadata.get("axis_alignment_required")
            else orientation_error_rad(actual=relative_pose(parent=pose_a, child=pose_b), expected=Pose())
        )
        residual = ConstraintResidual(
            constraint_id=closure.closure_id,
            time_s=0.0,
            position_residual_m=position,
            orientation_residual_rad=orientation,
        )
        residuals.append(residual)
        if position > closure.position_tolerance_m or orientation > closure.orientation_tolerance_rad:
            closure_issues.append(
                SimIssue(
                    code="KINCHECK-CLOSURE-INITIAL-POSE-MISMATCH",
                    severity="error",
                    stage="kinematics.closure",
                    message="The authored component pose does not satisfy a Closure tolerance.",
                    object_ids=(closure.closure_id,),
                    suggested_actions=("Regenerate the authored closed pose before solving.",),
                )
            )
    return ClosureReport(
        passed=not any(issue.severity == "error" for issue in closure_issues),
        residuals=tuple(residuals),
        issues=tuple(closure_issues),
    )


def _axis_alignment_error(actual_a: Pose, actual_b: Pose) -> float:
    axis_a = rotate_vector(pose=actual_a, vector=(0.0, 0.0, 1.0))
    axis_b = rotate_vector(pose=actual_b, vector=(0.0, 0.0, 1.0))
    dot = abs(sum(axis_a[index] * axis_b[index] for index in range(3)))
    return math.acos(max(-1.0, min(1.0, dot)))


def _raise_unimplemented(
    *, capability: str, object_ids: Sequence[str] = (), operation: str = "kinematics.capability"
) -> NoReturn:
    """Fail a declared public capability without returning an ambiguous ``None``."""

    message = "This kinematics capability is not implemented in the current release."
    action = "Use solve_motion() for supported time-domain motion, or provide this capability externally."
    report = DiagnosticReport(
        issues=(
            SimIssue(
                code="KINCHECK-KIN-CAPABILITY-UNIMPLEMENTED",
                severity="error",
                stage="kinematics.capability",
                message=message,
                object_ids=tuple(object_ids),
                evidence=(Evidence(key="missing_capability", actual=capability),),
                suggested_actions=(action,),
            ),
        ),
        operation=operation,
        status="capability_failed",
    )
    raise BackendCapabilityError(
        code="KINCHECK-KIN-CAPABILITY-UNIMPLEMENTED",
        message=message,
        report=report,
        operation=operation,
        missing_capabilities=(capability,),
    )


def solve_position(
    *,
    assembly: AssemblyModel,
    joint_positions: Mapping[str, float] | None = None,
    pose_targets: Sequence[PoseTarget] = (),
    options: PositionSolveOptions | Mapping[str, Any] | None = None,
) -> PositionResult:
    """Solve one kinematic state without starting a time-domain backend."""

    assembly_validation = validate_assembly(assembly=assembly)
    topology_validation = validate_topology(assembly=assembly)
    validation_issues = tuple(
        issue
        for issue in (*assembly_validation.issues, *topology_validation.issues)
        if issue.severity == "error"
    )
    if validation_issues:
        raise AssemblyValidationError(
            code="KINCHECK-ASSEMBLY-VALIDATION-FAILED",
            message="Assembly validation failed before position solving.",
            report=DiagnosticReport(issues=validation_issues),
        )
    try:
        normalized_joint_positions = {
            str(key): float(value)
            for key, value in (joint_positions or {}).items()
        }
    except (AttributeError, TypeError, ValueError) as error:
        issue = SimIssue(
            code="KINCHECK-KIN-POSITION-VALUE-INVALID",
            severity="error",
            stage="kinematics.position",
            message="Joint positions must be a mapping of IDs to numeric values.",
            object_ids=(assembly.assembly_id,),
            evidence=(Evidence(key="joint_positions", actual=joint_positions),),
        )
        return PositionResult(passed=False, joint_positions={}, component_poses={}, issues=(issue,))
    try:
        normalized_options = (
            PositionSolveOptions(**dict(options))
            if isinstance(options, Mapping)
            else options
        )
    except (TypeError, ValueError) as error:
        message = str(error)
        code = (
            "KINCHECK-KIN-POSITION-TOLERANCE-INVALID"
            if "position_tolerance_m" in message
            else "KINCHECK-KIN-ORIENTATION-TOLERANCE-INVALID"
            if "orientation_tolerance_rad" in message
            else "KINCHECK-KIN-POSITION-OPTIONS-INVALID"
        )
        issue = SimIssue(
            code=code,
            severity="error",
            stage="kinematics.position",
            message=message,
            object_ids=(assembly.assembly_id,),
            evidence=(Evidence(key="options", actual=dict(options) if isinstance(options, Mapping) else options),),
        )
        return PositionResult(
            passed=False,
            joint_positions={},
            component_poses={},
            issues=(issue,),
        )
    status, positions, poses, residuals, issues = solve_position_core(
        assembly=assembly,
        joint_positions=normalized_joint_positions,
        pose_targets=pose_targets,
        options=normalized_options,
    )
    return PositionResult(
        passed=status == "converged" and not any(issue.severity == "error" for issue in issues),
        joint_positions=positions,
        component_poses=poses,
        residuals=residuals,
        issues=issues,
    )


def _backend_failure(*, scenario: Scenario, cause: BaseException, operation: str) -> BackendFailure:
    return BackendFailure(
        backend_id="solver",
        operation=operation,
        native_error_type=type(cause).__name__,
        native_message=str(cause),
        backend_version=None,
        failure_time_s=getattr(cause, "time_s", None),
    )


def _motion_from_backend(*, scenario: Scenario, backend_result: Any, options: KinematicSolveOptions | None = None) -> MotionResult:
    samples = tuple(backend_result.samples)
    if not samples:
        raise MotionSolveError(
            code="KINCHECK-KIN-EMPTY-RESULT",
            message="The backend returned no motion samples.",
            object_ids=(scenario.scenario_id,),
        )
    duration_s = float(scenario.duration_s or samples[-1].time_s)
    sample_period_s = float(scenario.sample_period_s or duration_s)

    def normalized_time(raw_time_s: float) -> float:
        raw = float(raw_time_s)
        if abs(raw - duration_s) <= 1e-9:
            return duration_s
        nearest = round(raw / sample_period_s) * sample_period_s
        return nearest if abs(raw - nearest) <= 1e-9 else raw

    times = tuple(normalized_time(item.time_s) for item in samples)
    joint_ids = tuple(sorted({joint_id for item in samples for joint_id in item.joint_positions}))

    def derivative(values: tuple[float, ...], index: int) -> float:
        if len(values) == 1:
            return 0.0
        if index == 0:
            return (values[1] - values[0]) / (times[1] - times[0])
        if index == len(values) - 1:
            return (values[-1] - values[-2]) / (times[-1] - times[-2])
        return (values[index + 1] - values[index - 1]) / (times[index + 1] - times[index - 1])

    joint_trajectories: list[JointTrajectory] = []
    for joint_id in joint_ids:
        positions = tuple(float(item.joint_positions.get(joint_id, 0.0)) for item in samples)
        velocities = tuple(float(item.joint_velocities.get(joint_id, 0.0)) for item in samples)
        accelerations = tuple(derivative(velocities, index) for index in range(len(samples)))
        joint_trajectories.append(
            JointTrajectory(
                joint_id=joint_id,
                times_s=times,
                positions=positions,
                velocities=velocities,
                accelerations=accelerations,
            )
        )
    limit_events = detect_limit_events(
        assembly=scenario.assembly,
        joint_trajectories=joint_trajectories,
    )

    component_ids = tuple(sorted({component_id for item in samples for component_id in item.component_poses}))
    trajectories: list[Trajectory] = []

    def spatial_series(field_name: str, key: Any) -> tuple[tuple[float, float, float], ...] | None:
        mappings = tuple(getattr(item, field_name, None) for item in samples)
        if any(mapping is None or key not in mapping for mapping in mappings):
            return None
        return tuple(tuple(float(axis) for axis in mapping[key]) for mapping in mappings)

    for component_id in component_ids:
        poses = tuple(
            Pose(
                position_m=tuple(item.component_poses[component_id].position_m),
                orientation_xyzw=tuple(item.component_poses[component_id].orientation_xyzw),
            )
            for item in samples
        )
        trajectories.append(
            Trajectory(
                component_id=component_id,
                times_s=times,
                poses=poses,
                linear_velocities_m_s=spatial_series(
                    "component_linear_velocities", component_id
                ),
                angular_velocities_rad_s=spatial_series(
                    "component_angular_velocities", component_id
                ),
                linear_accelerations_m_s2=spatial_series(
                    "component_linear_accelerations", component_id
                ),
                angular_accelerations_rad_s2=spatial_series(
                    "component_angular_accelerations", component_id
                ),
            )
        )
    connector_keys = tuple(sorted({key for item in samples for key in item.connector_poses}))
    for component_id, connector_id in connector_keys:
        poses = tuple(
            Pose(
                position_m=tuple(item.connector_poses[(component_id, connector_id)].position_m),
                orientation_xyzw=tuple(item.connector_poses[(component_id, connector_id)].orientation_xyzw),
            )
            for item in samples
        )
        trajectories.append(
            Trajectory(
                component_id=component_id,
                connector_id=connector_id,
                times_s=times,
                poses=poses,
                linear_velocities_m_s=spatial_series(
                    "connector_linear_velocities", (component_id, connector_id)
                ),
                angular_velocities_rad_s=spatial_series(
                    "connector_angular_velocities", (component_id, connector_id)
                ),
                linear_accelerations_m_s2=spatial_series(
                    "connector_linear_accelerations", (component_id, connector_id)
                ),
                angular_accelerations_rad_s2=spatial_series(
                    "connector_angular_accelerations", (component_id, connector_id)
                ),
            )
        )

    geometric_constraint_ids = tuple(
        sorted(
            {
                key
                for item in samples
                for key in (
                    set(getattr(item, "constraint_position_residuals", {}))
                    | set(getattr(item, "constraint_orientation_residuals", {}))
                )
            }
        )
    )
    residuals = tuple(
        ConstraintResidual(
            constraint_id=constraint_id,
            time_s=times[index],
            position_residual_m=abs(
                float(
                    getattr(sample, "constraint_position_residuals", {}).get(
                        constraint_id, 0.0
                    )
                )
            ),
            orientation_residual_rad=abs(
                float(
                    getattr(sample, "constraint_orientation_residuals", {}).get(
                        constraint_id, 0.0
                    )
                )
            ),
        )
        for index, sample in enumerate(samples)
        for constraint_id in geometric_constraint_ids
    )
    equation_definitions = {
        constraint.constraint_id: (str(constraint.constraint_type).lower(), "m")
        for constraint in scenario.assembly.constraints
        if str(constraint.constraint_type).lower() in {"gear", "belt", "rack_pinion"}
    }
    equation_definitions.update(
        {
            coupling.coupling_id: ("coupling", "rad")
            for coupling in scenario.assembly.couplings
        }
    )
    equation_residual_values: list[tuple[int, str, float]] = []
    for index, sample in enumerate(samples):
        explicit_values = getattr(sample, "constraint_equation_residuals", {})
        values = (
            explicit_values
            if explicit_values
            else getattr(sample, "constraint_residuals", {})
        )
        equation_residual_values.extend(
            (index, constraint_id, float(value))
            for constraint_id, value in sorted(values.items())
            if constraint_id in equation_definitions
        )
    equation_residuals = tuple(
        ConstraintEquationResidual(
            constraint_id=constraint_id,
            time_s=times[index],
            value=value,
            equation_type=equation_definitions[constraint_id][0],
            unit=equation_definitions[constraint_id][1],
        )
        for index, constraint_id, value in equation_residual_values
    )
    closure_ids = {closure.closure_id for closure in scenario.assembly.closures}
    closure_residuals = tuple(item for item in residuals if item.constraint_id in closure_ids)
    closure_statuses: dict[str, str] = {}
    closure_issues: list[SimIssue] = []
    closure_by_id = {closure.closure_id: closure for closure in scenario.assembly.closures}
    for closure_id, closure in closure_by_id.items():
        values = tuple(item for item in closure_residuals if item.constraint_id == closure_id)
        position_limit = closure.position_tolerance_m
        orientation_limit = closure.orientation_tolerance_rad
        passed = bool(values) and all(
            item.position_residual_m <= position_limit
            and item.orientation_residual_rad <= orientation_limit
            for item in values
        )
        closure_statuses[closure_id] = "passed" if passed else "violated"
        if not passed:
            closure_issues.append(
                SimIssue(
                    code="KINCHECK-CLOSURE-RESIDUAL-EXCEEDED",
                    severity="error",
                    stage="kinematics.solve",
                    message="A closed-loop residual exceeded its declared tolerance.",
                    object_ids=(scenario.scenario_id, closure_id),
                    suggested_actions=(
                        "Reduce the drive step or revise the initial pose and closure tolerances.",
                    ),
                )
            )
    solve_tolerances = {
        "position_residual_m": float(options.position_residual_tolerance_m) if options is not None else 1e-6,
        "orientation_residual_rad": float(options.orientation_residual_tolerance_rad) if options is not None else 1e-6,
        "linear_equation_residual_m": float(options.position_residual_tolerance_m) if options is not None else 1e-6,
        "angular_equation_residual_rad": float(options.orientation_residual_tolerance_rad) if options is not None else 1e-6,
    }
    ordinary_constraint_ids = {
        item.constraint_id for item in scenario.assembly.constraints
    }
    constraint_issues: list[SimIssue] = []
    for constraint_id in sorted(ordinary_constraint_ids):
        values = tuple(
            item for item in residuals if item.constraint_id == constraint_id
        )
        violating = tuple(
            item
            for item in values
            if item.position_residual_m
            > solve_tolerances["position_residual_m"]
            or item.orientation_residual_rad
            > solve_tolerances["orientation_residual_rad"]
        )
        if violating:
            first = min(violating, key=lambda item: item.time_s)
            constraint_issues.append(
                SimIssue(
                    code="KINCHECK-CONSTRAINT-GEOMETRIC-RESIDUAL-EXCEEDED",
                    severity="error",
                    stage="kinematics.solve",
                    message="A general constraint geometric residual exceeded the solve tolerance.",
                    object_ids=(scenario.scenario_id, constraint_id),
                    failure_time_s=first.time_s,
                    evidence=(
                        Evidence(
                            key="maximum_position_residual_m",
                            actual=max(item.position_residual_m for item in values),
                            expected=f"<= {solve_tolerances['position_residual_m']}",
                            unit="m",
                        ),
                        Evidence(
                            key="maximum_orientation_residual_rad",
                            actual=max(item.orientation_residual_rad for item in values),
                            expected=f"<= {solve_tolerances['orientation_residual_rad']}",
                            unit="rad",
                        ),
                    ),
                    suggested_actions=(
                        "Inspect the imported connector placement and constraint geometry.",
                    ),
                )
            )
    equation_by_id: dict[str, list[ConstraintEquationResidual]] = {}
    for item in equation_residuals:
        equation_by_id.setdefault(item.constraint_id, []).append(item)
    for constraint_id, values in sorted(equation_by_id.items()):
        unit = values[0].unit
        tolerance = (
            solve_tolerances["linear_equation_residual_m"]
            if unit == "m"
            else solve_tolerances["angular_equation_residual_rad"]
        )
        violating = tuple(item for item in values if item.absolute_value > tolerance)
        if violating:
            first = min(violating, key=lambda item: item.time_s)
            constraint_issues.append(
                SimIssue(
                    code="KINCHECK-CONSTRAINT-EQUATION-RESIDUAL-EXCEEDED",
                    severity="error",
                    stage="kinematics.solve",
                    message="A transmission or coupling equation residual exceeded the solve tolerance.",
                    object_ids=(scenario.scenario_id, constraint_id),
                    failure_time_s=first.time_s,
                    evidence=(
                        Evidence(
                            key="maximum_absolute_residual",
                            actual=max(item.absolute_value for item in values),
                            expected=f"<= {tolerance}",
                            unit=unit,
                        ),
                        Evidence(
                            key="equation_type",
                            actual=values[0].equation_type,
                        ),
                    ),
                    suggested_actions=(
                        "Inspect the SI coefficients, initial state, and solver constraint settings.",
                    ),
                )
            )
    warning_issues = tuple(
        SimIssue(
            code="KINCHECK-BACKEND-WARNING",
            severity="warning",
            stage="kinematics.solve",
            message=warning,
            object_ids=(scenario.scenario_id,),
            suggested_actions=("Review the warning before relying on geometric phase details.",),
        )
        for warning in backend_result.warnings
    )
    if bool(getattr(backend_result, "metadata", {}).get("partial_due_nonfinite", False)):
        warning_issues = (*warning_issues, SimIssue(
            code="KINCHECK-KIN-NONFINITE-STATE-WARNED",
            severity="warning",
            stage="kinematics.solve",
            message="A non-finite backend state was detected; the last finite state was retained.",
            object_ids=(scenario.scenario_id,),
        ))
    tree = build_kinematic_tree(assembly=scenario.assembly)
    tree_payload = {
        "root_group_ids": list(tree.root_group_ids),
        "parent_component_id": dict(tree.parent_component_id),
        "parent_group_id": dict(tree.parent_group_id),
        "depth_by_component_id": dict(tree.depth_by_component_id),
        "tree_edges": [item.to_dict() for item in tree.tree_edges],
        "closure_edges": [item.to_dict() for item in tree.closure_edges],
        "disconnected_group_ids": list(tree.disconnected_group_ids),
    }
    component_by_id = {
        component.component_id: component for component in scenario.assembly.components
    }

    def pose_payload(pose: Pose) -> dict[str, list[float]]:
        return {
            "position_m": list(pose.position_m),
            "orientation_xyzw": list(pose.orientation_xyzw),
        }

    integration_samples = tuple(getattr(backend_result, "integration_samples", ()))
    integration_payload = tuple(
        {
            "time_s": float(item.time_s),
            "component_poses": {
                component_id: pose_payload(pose)
                for component_id, pose in sorted(item.component_poses.items())
            },
        }
        for item in integration_samples
    )
    typed_integration_samples = tuple(
        IntegrationSample(
            time_s=item["time_s"],
            component_poses={
                cid: Pose(position_m=payload["position_m"], orientation_xyzw=payload["orientation_xyzw"])
                for cid, payload in item["component_poses"].items()
            },
        )
        for item in integration_payload
    )

    requested_joint_ids = {item.joint_id for item in scenario.joint_result_requests}
    if requested_joint_ids:
        joint_trajectories = [item for item in joint_trajectories if item.joint_id in requested_joint_ids]
    requested_components = scenario.component_result_requests
    if requested_components and scenario.component_result_scope.value == "requested":
        allowed_components = {(item.component_id, item.connector_id) for item in requested_components}
        # A connector request also makes its owning component pose available.
        allowed_components |= {(item.component_id, None) for item in requested_components}
        trajectories = [item for item in trajectories if (item.component_id, item.connector_id) in allowed_components]

    def driver_target(driver: PositionDriver | SpeedDriver, time_s: float) -> float:
        interval = getattr(driver, "active_interval_s", None)
        if interval is not None and (time_s < interval[0] or time_s > interval[1]):
            return 0.0
        points = driver.profile.points
        boundary = getattr(getattr(scenario, "profile_boundary", "hold"), "value", getattr(scenario, "profile_boundary", "hold"))
        if time_s <= points[0].time_s:
            return 0.0 if boundary == "zero" and time_s < points[0].time_s else points[0].value
        if time_s >= points[-1].time_s:
            return 0.0 if boundary == "zero" and time_s > points[-1].time_s else points[-1].value
        for left, right in zip(points, points[1:]):
            if left.time_s <= time_s <= right.time_s:
                if driver.profile.interpolation.value == "step":
                    return left.value
                fraction = (time_s - left.time_s) / (right.time_s - left.time_s)
                return left.value + fraction * (right.value - left.value)
        return points[-1].value

    driver_trajectories: list[DriverTrajectory] = []
    trajectories_by_joint = {item.joint_id: item for item in joint_trajectories}
    for driver in (*scenario.position_drivers, *scenario.speed_drivers):
        trajectory = trajectories_by_joint.get(driver.joint_id)
        if trajectory is None:
            continue
        mode = "position" if isinstance(driver, PositionDriver) else "speed"
        actuals = trajectory.positions if mode == "position" else trajectory.velocities
        records = tuple(
            DriverTarget(joint_id=driver.joint_id, time_s=time_s, mode=mode, target=driver_target(driver, time_s), actual=actual, error=actual-driver_target(driver, time_s))
            for time_s, actual in zip(times, actuals)
        )
        driver_trajectories.append(DriverTrajectory(joint_id=driver.joint_id, mode=mode, samples=records))

    component_local_poses: dict[str, dict[str, list[float]]] = {}
    component_world_poses: dict[str, dict[str, list[float]]] = {}
    for component_id, component in component_by_id.items():
        parent_id = tree.parent_component_id.get(component_id)
        parent = component_by_id.get(parent_id) if parent_id is not None else None
        local_pose = (
            component.initial_pose
            if parent is None
            else relative_pose(parent=parent.initial_pose, child=component.initial_pose)
        )
        component_local_poses[component_id] = pose_payload(local_pose)
        component_world_poses[component_id] = pose_payload(component.initial_pose)
    issues = (*warning_issues, *closure_issues, *constraint_issues)
    status = (
        "partial"
        if closure_issues or constraint_issues or bool(getattr(backend_result, "metadata", {}).get("partial_due_nonfinite", False))
        else "completed_with_warnings"
        if warning_issues
        else "completed"
    )
    return MotionResult(
        scenario_id=scenario.scenario_id,
        assembly_id=scenario.assembly_id,
        status=status,
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        joint_trajectories=tuple(joint_trajectories),
        trajectories=tuple(trajectories),
        constraint_residuals=residuals,
        constraint_equation_residuals=equation_residuals,
        closure_residuals=closure_residuals,
        closure_statuses=closure_statuses,
        limit_events=limit_events,
        issues=issues,
        backend_id=backend_result.backend_name,
        backend_version=backend_result.backend_version,
        metadata={
            **dict(getattr(backend_result, "metadata", {})),
            "backend_model": dict(backend_result.model_summary),
            "component_result_scope": scenario.component_result_scope.value,
            "kinematic_tree": tree_payload,
            "component_local_poses": component_local_poses,
            "component_world_poses": component_world_poses,
            "integration_samples": integration_payload,
            "integration_sample_count": len(integration_payload),
            "integration_capture_enabled": scenario.capture_integration_steps,
            "integration_component_ids": scenario.integration_component_ids,
            "solve_tolerances": solve_tolerances,
        },
        integration_samples=typed_integration_samples,
        driver_trajectories=tuple(driver_trajectories),
    )


def solve_motion(*, scenario: Scenario, options: Any = None) -> MotionResult:
    """Validate and solve a Scenario through the configured private backend."""

    if options is not None and not isinstance(options, KinematicSolveOptions):
        if not isinstance(options, Mapping):
            issue = SimIssue(
                code="KINCHECK-KIN-OPTIONS-INVALID",
                severity="error",
                stage="kinematics.solve",
                message="options must be a KinematicSolveOptions instance or a mapping of its fields.",
                object_ids=(scenario.scenario_id,),
                evidence=(Evidence(key="options_type", actual=type(options).__name__, expected="KinematicSolveOptions or Mapping"),),
                suggested_actions=("Pass KinematicSolveOptions(...) or a mapping with documented fields.",),
            )
            raise BackendCapabilityError(
                code="KINCHECK-KIN-OPTIONS-INVALID",
                message="Invalid kinematic solve options.",
                report=DiagnosticReport(issues=(issue,)),
                object_ids=(scenario.scenario_id,),
                missing_capabilities=("valid options object",),
            )
        try:
            options = KinematicSolveOptions(**dict(options))
        except (TypeError, ValueError) as cause:
            raise BackendCapabilityError(code="KINCHECK-KIN-OPTIONS-UNSUPPORTED", message="Invalid or unsupported kinematic solve options.", object_ids=(scenario.scenario_id,), missing_capabilities=("typed KinematicSolveOptions",)) from cause
    assembly_validation = validate_assembly(assembly=scenario.assembly)
    topology_validation = validate_topology(assembly=scenario.assembly)
    validation_items: list[SimIssue] = []
    seen_validation_issues: set[tuple[str, str, tuple[str, ...]]] = set()
    for issue in (*assembly_validation.issues, *topology_validation.issues):
        key = (issue.stage, issue.code, issue.object_ids)
        if key not in seen_validation_issues:
            seen_validation_issues.add(key)
            validation_items.append(issue)
    validation_issues = tuple(validation_items)
    if any(issue.severity == "error" for issue in validation_issues):
        assembly_failed = any(
            issue.severity == "error" for issue in assembly_validation.issues
        )
        topology_failed = not assembly_failed and any(
            issue.severity == "error" and issue.stage == "assembly.topology"
            for issue in validation_issues
        )
        raise AssemblyValidationError(
            code=(
                "KINCHECK-ASSEMBLY-TOPOLOGY-VALIDATION-FAILED"
                if topology_failed
                else "KINCHECK-ASSEMBLY-VALIDATION-FAILED"
            ),
            message=(
                "Assembly topology validation failed before motion solving."
                if topology_failed
                else "Assembly validation failed before motion solving."
            ),
            report=DiagnosticReport(issues=validation_issues),
        )
    validation = validate_scenario(scenario=scenario)
    if not validation.passed:
        capability_issues = tuple(item for item in validation.issues if item.code.endswith("CAPABILITY-UNSUPPORTED"))
        if capability_issues:
            raise BackendCapabilityError(
                code="KINCHECK-KIN-BACKEND-CAPABILITY",
                message="The requested Joint capability is not supported by the backend.",
                report=DiagnosticReport(issues=capability_issues, status="capability_failed"),
                object_ids=tuple(oid for item in capability_issues for oid in item.object_ids),
                missing_capabilities=tuple(sorted({str(item.evidence[0].actual) for item in capability_issues if item.evidence})),
            )
        raise ScenarioValidationError(
            code="KINCHECK-SCENARIO-VALIDATION-FAILED",
            message="Scenario validation failed before motion solving.",
            report=DiagnosticReport(issues=validation.issues),
        )
    try:
        from ._backends import (
            BackendCapabilityFailure,
            BackendCompileFailure,
            BackendInitialStateFailure,
            BackendUnavailable,
            BackendSolveFailure,
            solve_scenario,
        )
        try:
            backend_result = solve_scenario(scenario=scenario, **({"options": options} if options is not None else {}))
        except BackendInitialStateFailure as cause:
            details = dict(getattr(cause, "details", {}))
            message = "Initial Joint states are inconsistent with the model constraints."
            issue = SimIssue(
                code="KINCHECK-SCENARIO-INITIAL-STATE-INCONSISTENT",
                severity="error",
                stage="scenario.initial_state",
                message=message,
                object_ids=tuple(
                    getattr(cause, "object_ids", (scenario.scenario_id,))
                ),
                evidence=(
                    Evidence(key="native_error_type", actual=type(cause).__name__),
                    Evidence(
                        key="initial_state",
                        actual=details.get("initial_state", details),
                        expected=(
                            "A consistent linear system whose residual norm is at most 1e-9"
                        ),
                    ),
                ),
                suggested_actions=(
                    "Make all initial Joint targets that share internal coordinates mutually consistent.",
                ),
            )
            report = DiagnosticReport(
                issues=(issue,),
                metadata=details,
            )
            raise ScenarioValidationError(
                code="KINCHECK-SCENARIO-INITIAL-STATE-INCONSISTENT",
                message=message,
                report=report,
                details=details,
            ) from cause
        except BackendUnavailable as cause:
            failure = _backend_failure(scenario=scenario, cause=cause, operation="load")
            report = DiagnosticReport(
                issues=(SimIssue(
                    code="KINCHECK-BACKEND-UNAVAILABLE",
                    severity="error",
                    stage="backend",
                    message="The backend is unavailable.",
                    object_ids=(scenario.scenario_id,),
                    suggested_actions=("Install the declared physics backend dependency and retry.",),
                ),),
                backend_failure=failure,
            )
            raise BackendUnavailableError(
                code="KINCHECK-BACKEND-UNAVAILABLE",
                message="The backend is unavailable.",
                report=report,
                backend_failure=failure,
            ) from cause
        except BackendCapabilityFailure as cause:
            details = dict(getattr(cause, "details", {}))
            message = "The requested Assembly or Scenario capability is not supported by the backend."
            issue = SimIssue(
                code="KINCHECK-KIN-BACKEND-CAPABILITY",
                severity="error",
                stage="backend.compile",
                message=message,
                object_ids=tuple(getattr(cause, "object_ids", (scenario.scenario_id,))),
                evidence=(Evidence(key="native_error_type", actual=type(cause).__name__),),
                suggested_actions=("Change the explicit Assembly or Scenario capability request.",),
            )
            report = DiagnosticReport(issues=(issue,), metadata=details)
            raise BackendCapabilityError(
                code="KINCHECK-KIN-BACKEND-CAPABILITY",
                message=message,
                report=report,
                missing_capabilities=tuple(sorted(str(key) for key in details)) or ("requested_capability",),
                details={"native_error_type": type(cause).__name__, "backend_details": details},
            ) from cause
        except BackendCompileFailure as cause:
            failure = _backend_failure(scenario=scenario, cause=cause, operation="compile")
            report = DiagnosticReport(
                issues=(SimIssue(
                    code="KINCHECK-KIN-COMPILE-FAILED",
                    severity="error",
                    stage="backend.compile",
                    message="The physics backend model could not be compiled.",
                    object_ids=(scenario.scenario_id,),
                ),),
                backend_failure=failure,
            )
            raise MotionSolveError(
                code="KINCHECK-KIN-COMPILE-FAILED",
                message="The physics backend model could not be compiled.",
                report=report,
                backend_failure=failure,
            ) from cause
        except BackendSolveFailure as cause:
            failure = _backend_failure(scenario=scenario, cause=cause, operation="step")
            last_valid = None
            raw_samples = tuple(getattr(cause, "last_valid_samples", ()))
            if raw_samples:
                try:
                    from dataclasses import replace
                    partial_backend = type("_PartialBackend", (), {
                        "samples": raw_samples,
                        "integration_samples": (),
                        "warnings": (),
                        "metadata": {},
                        "model_summary": {},
                        "backend_name": "solver",
                        "backend_version": "unknown",
                    })()
                    candidate = _motion_from_backend(scenario=scenario, backend_result=partial_backend, options=options)
                    issue_for_partial = SimIssue(code="KINCHECK-KIN-SOLVE-FAILED", severity="error", stage="backend.solve", message="physics backend failed while stepping the Scenario.", object_ids=(scenario.scenario_id,), failure_time_s=getattr(cause, "time_s", None))
                    last_valid = replace(candidate, status="partial", issues=(*candidate.issues, issue_for_partial))
                except Exception:
                    last_valid = None
            report = DiagnosticReport(
                issues=(SimIssue(
                    code="KINCHECK-KIN-SOLVE-FAILED",
                    severity="error",
                    stage="backend.solve",
                    message="physics backend failed while stepping the Scenario.",
                    object_ids=(scenario.scenario_id,),
                    failure_time_s=getattr(cause, "time_s", None),
                ),),
                failure_time_s=getattr(cause, "time_s", None),
                last_valid_result=last_valid,
                backend_failure=failure,
            )
            raise MotionSolveError(
                code="KINCHECK-KIN-SOLVE-FAILED",
                message="physics backend failed while stepping the Scenario.",
                report=report,
                failure_time_s=getattr(cause, "time_s", None),
                last_valid_result=last_valid,
                backend_failure=failure,
            ) from cause
        return _motion_from_backend(scenario=scenario, backend_result=backend_result, options=options)
    except KinCheckError:
        raise
    except Exception as cause:
        failure = _backend_failure(scenario=scenario, cause=cause, operation="solve_motion")
        report = DiagnosticReport(
            issues=(SimIssue(
                code="KINCHECK-KIN-UNEXPECTED",
                severity="error",
                stage="kinematics.solve",
                message="Unexpected failure in the motion adapter.",
                object_ids=(scenario.scenario_id,),
            ),),
            backend_failure=failure,
        )
        raise MotionSolveError(
            code="KINCHECK-KIN-UNEXPECTED",
            message="Unexpected failure in the motion adapter.",
            report=report,
            backend_failure=failure,
        ) from cause


def try_solve_motion(*, scenario: Scenario, options: Any = None) -> SolveAttempt:
    """Return a structured, non-throwing outcome for expected model failures."""

    try:
        motion = solve_motion(scenario=scenario, options=options)
    except KinCheckError as failure:
        status = {
            AssemblyValidationError: "validation_failed",
            ScenarioValidationError: "validation_failed",
            BackendUnavailableError: "capability_failed",
            BackendCapabilityError: "capability_failed",
            MotionSolveError: "failed",
        }.get(type(failure), "failed")
        return SolveAttempt(
            status=status,  # type: ignore[arg-type]
            succeeded=False,
            motion_result=None,
            last_valid_result=failure.last_valid_result if isinstance(failure, MotionSolveError) else None,
            report=failure.report,
            failure=failure,
        )
    report = DiagnosticReport(
        issues=motion.issues,
        last_valid_result=motion if motion.status == "partial" else None,
        operation="try_solve_motion",
        status="partial" if motion.status == "partial" else "passed",
        metadata={"scenario_id": scenario.scenario_id},
    )
    if motion.status == "partial":
        return SolveAttempt(
            status="partial",
            succeeded=False,
            motion_result=None,
            last_valid_result=motion,
            report=report,
            failure=None,
        )
    return SolveAttempt(status=motion.status, succeeded=True, motion_result=motion, last_valid_result=None, report=report, failure=None)


def check_reachability(*, assembly: AssemblyModel, target: Any, options: Any = None, joint_positions: Mapping[str, float] | None = None, solver_options: Any = None) -> ReachabilityResult:
    """Check whether one requested Pose can be satisfied by the assembly."""

    from .kinematics_analysis import check_reachability as _check_reachability

    return _check_reachability(assembly=assembly, target=target, options=options, joint_positions=joint_positions, solver_options=solver_options)


def find_singularities(*, motion_result: Any, assembly: AssemblyModel, options: Any = None) -> SingularityReport:
    """Classify recorded motion samples by their Jacobian conditioning."""

    from .kinematics_analysis import find_singularities as _find_singularities

    return _find_singularities(motion_result=motion_result, assembly=assembly, options=options)


def compute_workspace(*, assembly: AssemblyModel, target: Any, options: Any, solver_options: Any = None) -> Any:
    """Enumerate a finite deterministic set of joint configurations."""

    from .kinematics_analysis import compute_workspace as _compute_workspace

    return _compute_workspace(assembly=assembly, target=target, options=options, solver_options=solver_options)


def trace_connector_path(*, motion_result: Any, component_id: str, connector_id: str) -> Any:
    """Summarize one Connector trajectory already stored in a MotionResult."""

    from .kinematics_analysis import trace_connector_path as _trace_connector_path

    return _trace_connector_path(motion_result=motion_result, component_id=component_id, connector_id=connector_id)


def write_motion_result(*, motion_result: MotionResult, path: str | Path) -> None:
    from .result import write_motion_result as write_result

    write_result(motion_result=motion_result, path=path)


def solve_inverse_kinematics(*, assembly: AssemblyModel, target: Any, initial_joint_positions: Mapping[str, float] | None = None, joint_limits: Mapping[str, Sequence[float]] | None = None, solution_selection: str = "first") -> Any:
    """Explicit capability boundary for the not-yet-implemented general IK solver."""
    target_id = getattr(target, "component_id", None)
    if not target_id:
        target_id = getattr(getattr(target, "target", None), "component_id", "")
    _raise_unimplemented(
        capability="general_inverse_kinematics",
        object_ids=(str(target_id),) if target_id else (),
        operation="solve_inverse_kinematics",
    )


__all__ = [
    "KinematicSolveOptions",
    "KinematicCapabilities",
    "ClosureReport",
    "ConnectorPathResult",
    "DofReport",
    "JacobianOptions",
    "JacobianResult",
    "MobilityReport",
    "PoseTarget",
    "PositionSolveOptions",
    "ReachabilityOptions",
    "PositionResult",
    "ReachabilityResult",
    "SingularityReport",
    "SingularityOptions",
    "SingularitySample",
    "SolveAttempt",
    "TargetReference",
    "WorkspaceOptions",
    "WorkspaceResult",
    "WorkspaceSample",
    "analyze_dofs",
    "backend_capabilities",
    "analyze_mobility",
    "check_reachability",
    "compute_workspace",
    "compute_jacobian",
    "find_singularities",
    "solve_motion",
    "solve_position",
    "trace_connector_path",
    "try_solve_motion",
    "validate_closures",
    "verify_transmission_ratio",
    "write_motion_result",
    "solve_inverse_kinematics",
]
