"""Backend-independent motion result models and deterministic readers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

from .assembly import Pose, Vector3
from .diagnostics import AgentReadableResult, DiagnosticReport, Evidence, SimIssue


Direction = Literal["same", "opposite"]
MotionStatus = Literal["completed", "completed_with_warnings", "partial"]
LimitSide = Literal["lower", "upper"]
LimitEventType = Literal["reached", "exceeded"]
ConstraintEquationType = Literal["gear", "belt", "rack_pinion", "coupling"]
ConstraintEquationUnit = Literal["m", "rad"]

class _JointTrajectoryTuple(tuple["JointTrajectory", ...]):
    """Ordered collection with ID lookup for internal verifier compatibility."""

    def get(self, joint_id: str, default: Any = None) -> "JointTrajectory | Any":
        return next((item for item in self if item.joint_id == joint_id), default)


def _require_id(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _vector(value: Sequence[float], name: str) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{name} must contain three values")
    return tuple(_finite(item, name) for item in value)  # type: ignore[return-value]


def _times(value: Sequence[float], name: str = "times_s") -> tuple[float, ...]:
    result = tuple(_finite(item, name) for item in value)
    if not result:
        raise ValueError(f"{name} must contain at least one sample")
    if result[0] < 0.0 or any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError(f"{name} must be non-negative and strictly increasing")
    return result


def _values(
    value: Sequence[float], *, sample_count: int, name: str
) -> tuple[float, ...]:
    result = tuple(_finite(item, name) for item in value)
    if len(result) != sample_count:
        raise ValueError(f"{name} must have one value per time sample")
    return result


def _vectors(
    value: Sequence[Sequence[float]], *, sample_count: int, name: str
) -> tuple[Vector3, ...]:
    result = tuple(_vector(item, name) for item in value)
    if len(result) != sample_count:
        raise ValueError(f"{name} must have one vector per time sample")
    return result


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if hasattr(value, "to_dict"):
        return _json_value(value.to_dict())
    if is_dataclass(value):
        return _json_value(asdict(value))
    return repr(value)


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({
        str(key): (
            _freeze_mapping(item)
            if isinstance(item, Mapping)
            else tuple(item) if isinstance(item, list) else item
        )
        for key, item in value.items()
    })


@dataclass(frozen=True, slots=True, kw_only=True)
class JointState:
    """One scalar joint sample in SI units (radians or metres)."""

    joint_id: str
    time_s: float
    position: float
    velocity: float
    acceleration: float

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        for name in ("time_s", "position", "velocity", "acceleration"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def position_rad_or_m(self) -> float:
        return self.position

    @property
    def velocity_rad_s_or_m_s(self) -> float:
        return self.velocity

    @property
    def acceleration_rad_s2_or_m_s2(self) -> float:
        return self.acceleration


@dataclass(frozen=True, slots=True, kw_only=True)
class JointTrajectory:
    """Complete sampled state of one revolute or prismatic joint."""

    joint_id: str
    times_s: tuple[float, ...]
    positions: tuple[float, ...]
    velocities: tuple[float, ...]
    accelerations: tuple[float, ...]

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        times = _times(self.times_s)
        object.__setattr__(self, "times_s", times)
        object.__setattr__(
            self,
            "positions",
            _values(self.positions, sample_count=len(times), name="positions"),
        )
        object.__setattr__(
            self,
            "velocities",
            _values(self.velocities, sample_count=len(times), name="velocities"),
        )
        object.__setattr__(
            self,
            "accelerations",
            _values(self.accelerations, sample_count=len(times), name="accelerations"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))

    @property
    def samples(self) -> tuple[JointState, ...]:
        """Expose typed samples for generic verification code."""

        return tuple(
            JointState(
                joint_id=self.joint_id,
                time_s=time,
                position=position,
                velocity=velocity,
                acceleration=acceleration,
            )
            for time, position, velocity, acceleration in zip(
                self.times_s, self.positions, self.velocities, self.accelerations
            )
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ComponentState:
    component_id: str
    time_s: float
    pose: Pose
    linear_velocity_m_s: Vector3 | None = None
    angular_velocity_rad_s: Vector3 | None = None
    linear_acceleration_m_s2: Vector3 | None = None
    angular_acceleration_rad_s2: Vector3 | None = None

    def __post_init__(self) -> None:
        _require_id(self.component_id, "component_id")
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        if not isinstance(self.pose, Pose):
            raise TypeError("pose must be a Pose")
        for name in (
            "linear_velocity_m_s",
            "angular_velocity_rad_s",
            "linear_acceleration_m_s2",
            "angular_acceleration_rad_s2",
        ):
            raw = getattr(self, name)
            object.__setattr__(self, name, None if raw is None else _vector(raw, name))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectorState:
    component_id: str
    connector_id: str
    time_s: float
    pose: Pose
    linear_velocity_m_s: Vector3 | None = None
    angular_velocity_rad_s: Vector3 | None = None
    linear_acceleration_m_s2: Vector3 | None = None
    angular_acceleration_rad_s2: Vector3 | None = None

    def __post_init__(self) -> None:
        _require_id(self.component_id, "component_id")
        _require_id(self.connector_id, "connector_id")
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        if not isinstance(self.pose, Pose):
            raise TypeError("pose must be a Pose")
        for name in (
            "linear_velocity_m_s",
            "angular_velocity_rad_s",
            "linear_acceleration_m_s2",
            "angular_acceleration_rad_s2",
        ):
            raw = getattr(self, name)
            object.__setattr__(self, name, None if raw is None else _vector(raw, name))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class Trajectory:
    """Rigid-body trajectory for a component or one of its connectors."""

    component_id: str
    times_s: tuple[float, ...]
    poses: tuple[Pose, ...]
    connector_id: str | None = None
    linear_velocities_m_s: tuple[Vector3, ...] | None = None
    angular_velocities_rad_s: tuple[Vector3, ...] | None = None
    linear_accelerations_m_s2: tuple[Vector3, ...] | None = None
    angular_accelerations_rad_s2: tuple[Vector3, ...] | None = None

    def __post_init__(self) -> None:
        _require_id(self.component_id, "component_id")
        if self.connector_id is not None:
            _require_id(self.connector_id, "connector_id")
        times = _times(self.times_s)
        poses = tuple(self.poses)
        if len(poses) != len(times) or any(not isinstance(item, Pose) for item in poses):
            raise ValueError("poses must contain one Pose per time sample")
        object.__setattr__(self, "times_s", times)
        object.__setattr__(self, "poses", poses)
        for name in (
            "linear_velocities_m_s",
            "angular_velocities_rad_s",
            "linear_accelerations_m_s2",
            "angular_accelerations_rad_s2",
        ):
            raw = getattr(self, name)
            normalized = (
                None
                if raw is None
                else _vectors(raw, sample_count=len(times), name=name)
            )
            object.__setattr__(self, name, normalized)

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class IntegrationSample:
    """Typed snapshot captured at an internal solver integration step."""
    time_s: float
    component_poses: Mapping[str, Pose]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        if self.time_s < 0:
            raise ValueError("time_s must be non-negative")
        if any(not isinstance(pose, Pose) for pose in self.component_poses.values()):
            raise TypeError("component_poses must contain Pose values")
        object.__setattr__(self, "component_poses", MappingProxyType(dict(self.component_poses)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "time_s": self.time_s,
            "component_poses": {
                k: {
                    "position_m": list(v.position_m),
                    "orientation_xyzw": list(v.orientation_xyzw),
                }
                for k, v in self.component_poses.items()
            },
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class DriverTarget:
    """One declared driver target and the corresponding measured joint value."""
    joint_id: str
    time_s: float
    mode: Literal["position", "speed"]
    target: float
    actual: float
    error: float

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        if self.mode not in {"position", "speed"}:
            raise ValueError("mode must be position or speed")
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        object.__setattr__(self, "target", _finite(self.target, "target"))
        object.__setattr__(self, "actual", _finite(self.actual, "actual"))
        object.__setattr__(self, "error", _finite(self.error, "error"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class DriverTrajectory:
    """Time ordered target/actual records for one joint driver."""
    joint_id: str
    mode: Literal["position", "speed"]
    samples: tuple[DriverTarget, ...]

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        if self.mode not in {"position", "speed"}:
            raise ValueError("mode must be position or speed")
        samples = tuple(self.samples)
        if any(item.joint_id != self.joint_id or item.mode != self.mode for item in samples):
            raise ValueError("driver samples must match joint_id and mode")
        if any(right.time_s <= left.time_s for left, right in zip(samples, samples[1:])):
            raise ValueError("driver samples must be strictly increasing")
        object.__setattr__(self, "samples", samples)

    def to_dict(self) -> dict[str, Any]:
        return {"joint_id": self.joint_id, "mode": self.mode, "samples": [item.to_dict() for item in self.samples]}


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstraintResidual:
    constraint_id: str
    time_s: float
    position_residual_m: float
    orientation_residual_rad: float

    def __post_init__(self) -> None:
        _require_id(self.constraint_id, "constraint_id")
        for name in ("time_s", "position_residual_m", "orientation_residual_rad"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if min(self.time_s, self.position_residual_m, self.orientation_residual_rad) < 0.0:
            raise ValueError("constraint residual fields must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstraintEquationResidual:
    """Signed residual of a gear, belt, rack-pinion, or coupling equation."""

    constraint_id: str
    time_s: float
    value: float
    absolute_value: float | None = None
    unit: ConstraintEquationUnit
    equation_type: ConstraintEquationType

    def __post_init__(self) -> None:
        _require_id(self.constraint_id, "constraint_id")
        time_s = _finite(self.time_s, "time_s")
        value = _finite(self.value, "value")
        absolute_value = abs(value) if self.absolute_value is None else _finite(
            self.absolute_value, "absolute_value"
        )
        if time_s < 0.0 or absolute_value < 0.0:
            raise ValueError("time_s and absolute_value must be non-negative")
        if not math.isclose(absolute_value, abs(value), rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("absolute_value must equal abs(value)")
        if self.unit not in {"m", "rad"}:
            raise ValueError("unit must be m or rad")
        if self.equation_type not in {"gear", "belt", "rack_pinion", "coupling"}:
            raise ValueError("equation_type must be gear, belt, rack_pinion, or coupling")
        if self.equation_type in {"gear", "belt", "rack_pinion"} and self.unit != "m":
            raise ValueError("gear, belt, and rack_pinion equation residuals must use metres")
        if self.equation_type == "coupling" and self.unit != "rad":
            raise ValueError("coupling equation residuals must use radians")
        object.__setattr__(self, "time_s", time_s)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "absolute_value", absolute_value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class LimitEvent:
    joint_id: str
    time_s: float
    side: LimitSide
    event_type: LimitEventType
    position: float
    limit_position: float

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        if self.side not in {"lower", "upper"}:
            raise ValueError("side must be 'lower' or 'upper'")
        if self.event_type not in {"reached", "exceeded"}:
            raise ValueError("event_type must be 'reached' or 'exceeded'")
        for name in ("time_s", "position", "limit_position"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class InterferenceEvent:
    component_a_id: str
    component_b_id: str
    time_s: float
    penetration_depth_m: float
    position_m: Vector3 | None = None

    def __post_init__(self) -> None:
        _require_id(self.component_a_id, "component_a_id")
        _require_id(self.component_b_id, "component_b_id")
        if self.component_a_id == self.component_b_id:
            raise ValueError("interference components must be distinct")
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        object.__setattr__(
            self,
            "penetration_depth_m",
            _finite(self.penetration_depth_m, "penetration_depth_m"),
        )
        if self.time_s < 0.0 or self.penetration_depth_m < 0.0:
            raise ValueError("interference time and penetration must be non-negative")
        if self.position_m is not None:
            object.__setattr__(self, "position_m", _vector(self.position_m, "position_m"))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class InterferenceResult(AgentReadableResult):
    events: tuple[InterferenceEvent, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.events

    @property
    def issues(self) -> tuple[SimIssue, ...]:
        if not self.events:
            return ()
        first = self.events[0]
        return (
            SimIssue(
                code="KINCHECK-CLEARANCE-INTERFERENCE-DETECTED",
                severity="error",
                stage="clearance.interference",
                message="Interference was detected between recorded components.",
                object_ids=tuple(
                    dict.fromkeys(
                        component_id
                        for event in self.events
                        for component_id in (event.component_a_id, event.component_b_id)
                    )
                ),
                evidence=(
                    Evidence(key="event_count", actual=len(self.events), expected=0),
                    Evidence(
                        key="maximum_penetration_depth_m",
                        actual=max(item.penetration_depth_m for item in self.events),
                        expected=0.0,
                        unit="m",
                    ),
                ),
                failure_time_s=first.time_s,
                suggested_actions=(
                    "Revise the component geometry or motion path, then run the interference check again.",
                ),
            ),
        )

    def __post_init__(self) -> None:
        events = tuple(self.events)
        if any(not isinstance(item, InterferenceEvent) for item in events):
            raise TypeError("events must contain InterferenceEvent values")
        object.__setattr__(
            self,
            "events",
            tuple(sorted(events, key=lambda item: (item.time_s, item.component_a_id, item.component_b_id))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "check_interference",
            "status": "passed" if self.passed else "failed",
            "events": [item.to_dict() for item in self.events],
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionResult(AgentReadableResult):
    """Stable output of any KinCheckAPI motion backend."""

    scenario_id: str
    assembly_id: str
    status: MotionStatus
    start_time_s: float
    end_time_s: float
    sample_times_s: tuple[float, ...]
    joint_trajectories: tuple[JointTrajectory, ...] | Mapping[str, JointTrajectory] = ()
    trajectories: tuple[Trajectory, ...] = ()
    constraint_residuals: tuple[ConstraintResidual, ...] = ()
    constraint_equation_residuals: tuple[ConstraintEquationResidual, ...] = ()
    closure_residuals: tuple[ConstraintResidual, ...] = ()
    closure_statuses: Mapping[str, str] = field(default_factory=dict)
    limit_events: tuple[LimitEvent, ...] = ()
    issues: tuple[SimIssue, ...] = ()
    backend_id: str | None = None
    backend_version: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    integration_samples: tuple[IntegrationSample, ...] = ()
    driver_trajectories: tuple[DriverTrajectory, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status in {"completed", "completed_with_warnings"} and not any(
            item.severity == "error" for item in self.issues
        )

    def __post_init__(self) -> None:
        _require_id(self.scenario_id, "scenario_id")
        _require_id(self.assembly_id, "assembly_id")
        if self.status not in {"completed", "completed_with_warnings", "partial"}:
            raise ValueError("status must be completed, completed_with_warnings, or partial")
        times = _times(self.sample_times_s, "sample_times_s")
        start = _finite(self.start_time_s, "start_time_s")
        end = _finite(self.end_time_s, "end_time_s")
        if start != times[0] or end != times[-1]:
            raise ValueError("start_time_s and end_time_s must match the first and last sample")
        object.__setattr__(self, "sample_times_s", times)
        object.__setattr__(self, "start_time_s", start)
        object.__setattr__(self, "end_time_s", end)
        joint_values = (
            tuple(self.joint_trajectories.values())
            if isinstance(self.joint_trajectories, Mapping)
            else tuple(self.joint_trajectories)
        )
        if any(not isinstance(item, JointTrajectory) for item in joint_values):
            raise TypeError("joint_trajectories must contain JointTrajectory values")
        joints = _JointTrajectoryTuple(sorted(joint_values, key=lambda item: item.joint_id))
        trajectories = tuple(
            sorted(self.trajectories, key=lambda item: (item.component_id, item.connector_id or ""))
        )
        residuals = tuple(
            sorted(self.constraint_residuals, key=lambda item: (item.time_s, item.constraint_id))
        )
        equation_residuals = tuple(
            sorted(
                self.constraint_equation_residuals,
                key=lambda item: (item.time_s, item.constraint_id),
            )
        )
        if any(not isinstance(item, ConstraintEquationResidual) for item in equation_residuals):
            raise TypeError(
                "constraint_equation_residuals must contain ConstraintEquationResidual values"
            )
        closure_residuals = tuple(
            sorted(self.closure_residuals, key=lambda item: (item.time_s, item.constraint_id))
        )
        closure_statuses = dict(self.closure_statuses)
        if any(status not in {"passed", "violated", "not_converged"} for status in closure_statuses.values()):
            raise ValueError("closure_statuses values must be passed, violated, or not_converged")
        events = tuple(sorted(self.limit_events, key=lambda item: (item.time_s, item.joint_id)))
        issues = tuple(self.issues)
        if len({item.joint_id for item in joints}) != len(joints):
            raise ValueError("joint_trajectories must have unique Joint IDs")
        trajectory_keys = {(item.component_id, item.connector_id) for item in trajectories}
        if len(trajectory_keys) != len(trajectories):
            raise ValueError("trajectories must have unique component/connector IDs")
        if any(not isinstance(item, SimIssue) for item in issues):
            raise TypeError("issues must contain SimIssue values")
        has_warning = any(item.severity == "warning" for item in issues)
        has_error = any(item.severity == "error" for item in issues)
        if self.status == "completed" and (has_warning or has_error):
            raise ValueError("completed results cannot contain warnings or errors")
        if self.status == "completed_with_warnings" and (not has_warning or has_error):
            raise ValueError("completed_with_warnings requires warnings and cannot contain errors")
        object.__setattr__(self, "joint_trajectories", joints)
        object.__setattr__(self, "trajectories", trajectories)
        object.__setattr__(self, "constraint_residuals", residuals)
        object.__setattr__(self, "constraint_equation_residuals", equation_residuals)
        object.__setattr__(self, "closure_residuals", closure_residuals)
        object.__setattr__(self, "closure_statuses", _freeze_mapping(closure_statuses))
        object.__setattr__(self, "limit_events", events)
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        integration_samples = tuple(self.integration_samples)
        if any(not isinstance(item, IntegrationSample) for item in integration_samples):
            raise TypeError("integration_samples must contain IntegrationSample values")
        if any(right.time_s <= left.time_s for left, right in zip(integration_samples, integration_samples[1:])):
            raise ValueError("integration_samples times must be strictly increasing")
        object.__setattr__(self, "integration_samples", integration_samples)
        driver_trajectories = tuple(self.driver_trajectories)
        if any(not isinstance(item, DriverTrajectory) for item in driver_trajectories):
            raise TypeError("driver_trajectories must contain DriverTrajectory values")
        object.__setattr__(self, "driver_trajectories", driver_trajectories)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "assembly_id": self.assembly_id,
            "status": self.status,
            "passed": self.passed,
            "operation": "solve_motion",
            "start_time_s": self.start_time_s,
            "end_time_s": self.end_time_s,
            "sample_times_s": list(self.sample_times_s),
            "joint_trajectories": [item.to_dict() for item in self.joint_trajectories],
            "trajectories": [item.to_dict() for item in self.trajectories],
            "constraint_residuals": [item.to_dict() for item in self.constraint_residuals],
            "constraint_equation_residuals": [
                item.to_dict() for item in self.constraint_equation_residuals
            ],
            "closure_residuals": [item.to_dict() for item in self.closure_residuals],
            "closure_statuses": dict(self.closure_statuses),
            "limit_events": [item.to_dict() for item in self.limit_events],
            "issues": [item.to_dict() for item in self.issues],
            "backend_id": self.backend_id,
            "backend_version": self.backend_version,
            "metadata": _json_value(self.metadata),
            "integration_samples": [item.to_dict() for item in self.integration_samples],
            "driver_trajectories": [item.to_dict() for item in self.driver_trajectories],
        }

    def get_joint_trajectory(self, *, joint_id: str) -> JointTrajectory | None:
        return next(
            (item for item in self.joint_trajectories if item.joint_id == joint_id), None
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class JointExtrema:
    joint_id: str
    minimum_position: float
    maximum_position: float
    maximum_absolute_velocity: float
    maximum_absolute_acceleration: float

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        for name in (
            "minimum_position",
            "maximum_position",
            "maximum_absolute_velocity",
            "maximum_absolute_acceleration",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionSummary(AgentReadableResult):
    status: MotionStatus
    duration_s: float
    sample_count: int
    joint_extrema: tuple[JointExtrema, ...]
    maximum_position_residual_m: float
    maximum_orientation_residual_rad: float
    limit_event_count: int
    warning_count: int

    @property
    def passed(self) -> bool:
        return self.status in {"completed", "completed_with_warnings"}

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "passed": self.passed,
            "operation": "summarize_motion",
            "validation_status": "passed" if self.passed else "partial",
            "joint_extrema": [item.to_dict() for item in self.joint_extrema],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class _PlanetaryStageEvidence:
    stage_id: str
    sun_teeth: int
    planet_teeth: int
    ring_teeth: int
    measured_ratio: float | None
    expected_ratio: float | None
    relative_error: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class TransmissionRatioCheck(AgentReadableResult):
    passed: bool
    expected_ratio: float
    measured_ratio: float | None
    relative_error: float | None
    expected_direction: Direction
    measured_direction: Direction | None
    input_joint_id: str
    output_joint_id: str
    input_member: str | None = None
    output_member: str | None = None
    fixed_member: str | None = None
    sample_count: int = 0
    rejected_sample_count: int = 0
    start_time_s: float | None = None
    end_time_s: float | None = None
    stage_checks: tuple[_PlanetaryStageEvidence, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    issues: tuple[SimIssue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "verify_transmission_ratio",
            "status": "passed" if self.passed else "failed",
            "expected_ratio": self.expected_ratio,
            "measured_ratio": self.measured_ratio,
            "relative_error": self.relative_error,
            "expected_direction": self.expected_direction,
            "measured_direction": self.measured_direction,
            "input_joint_id": self.input_joint_id,
            "output_joint_id": self.output_joint_id,
            "input_member": self.input_member,
            "output_member": self.output_member,
            "fixed_member": self.fixed_member,
            "sample_count": self.sample_count,
            "rejected_sample_count": self.rejected_sample_count,
            "start_time_s": self.start_time_s,
            "end_time_s": self.end_time_s,
            "stage_checks": [item.to_dict() for item in self.stage_checks],
            "evidence": [item.to_dict() for item in self.evidence],
            "issues": [item.to_dict() for item in self.issues],
        }


def _bracket(*, times: tuple[float, ...], time_s: float) -> tuple[int, int, float]:
    time = _finite(time_s, "time_s")
    if time < times[0] or time > times[-1]:
        raise ValueError(f"time_s {time} is outside [{times[0]}, {times[-1]}]")
    if time == times[-1]:
        index = len(times) - 1
        return index, index, 0.0
    for right, right_time in enumerate(times[1:], start=1):
        if time <= right_time:
            left = right - 1
            if time == times[left]:
                return left, left, 0.0
            return left, right, (time - times[left]) / (right_time - times[left])
    raise AssertionError("unreachable time bracket")


def _lerp(left: float, right: float, weight: float) -> float:
    return left + (right - left) * weight


def _lerp_vector(left: Vector3, right: Vector3, weight: float) -> Vector3:
    return tuple(_lerp(a, b, weight) for a, b in zip(left, right))  # type: ignore[return-value]


def _lerp_pose(left: Pose, right: Pose, weight: float) -> Pose:
    left_q = left.orientation_xyzw
    right_q = right.orientation_xyzw
    if sum(a * b for a, b in zip(left_q, right_q)) < 0.0:
        right_q = tuple(-item for item in right_q)  # type: ignore[assignment]
    quaternion = tuple(_lerp(a, b, weight) for a, b in zip(left_q, right_q))
    norm = math.sqrt(sum(item * item for item in quaternion))
    normalized = tuple(item / norm for item in quaternion)
    return Pose(
        position_m=_lerp_vector(left.position_m, right.position_m, weight),
        orientation_xyzw=normalized,  # type: ignore[arg-type]
    )


def _find_joint(*, motion_result: MotionResult, joint_id: str) -> JointTrajectory:
    _require_id(joint_id, "joint_id")
    candidate = next(
        (item for item in motion_result.joint_trajectories if item.joint_id == joint_id), None
    )
    if candidate is None:
        raise KeyError(f"MotionResult has no requested Joint trajectory: {joint_id}")
    return candidate


def _find_trajectory(
    *, motion_result: MotionResult, component_id: str, connector_id: str | None
) -> Trajectory:
    _require_id(component_id, "component_id")
    if connector_id is not None:
        _require_id(connector_id, "connector_id")
    candidate = next(
        (
            item
            for item in motion_result.trajectories
            if item.component_id == component_id and item.connector_id == connector_id
        ),
        None,
    )
    if candidate is None:
        label = component_id if connector_id is None else f"{component_id}/{connector_id}"
        raise KeyError(f"MotionResult has no requested trajectory: {label}")
    return candidate


def _available_ids(*, motion_result: MotionResult, kind: str) -> tuple[str, ...]:
    if not isinstance(motion_result, MotionResult):
        return ()
    if kind == "joint":
        return tuple(item.joint_id for item in motion_result.joint_trajectories)
    if kind == "component":
        return tuple(
            item.component_id
            for item in motion_result.trajectories
            if item.connector_id is None
        )
    if kind == "connector":
        return tuple(
            f"{item.component_id}/{item.connector_id}"
            for item in motion_result.trajectories
            if item.connector_id is not None
        )
    if kind == "constraint":
        return tuple(item.constraint_id for item in motion_result.constraint_residuals)
    if kind == "limit_joint":
        return tuple(item.joint_id for item in motion_result.limit_events)
    return ()


def _result_query_error(
    *,
    cause: Exception,
    operation: str,
    requested_id: str | None = None,
    available_ids: tuple[str, ...] = (),
    code: str = "KINCHECK-RESULT-QUERY-INVALID",
) -> "KinCheckError":
    """Map reader failures to the public structured-error boundary."""

    # Imported lazily because ``errors`` itself imports diagnostics.
    from .errors import KinCheckError

    object_ids = (requested_id,) if requested_id else ()
    evidence = (
        Evidence(key="requested_id", actual=requested_id),
        Evidence(key="available_ids", actual=available_ids),
        Evidence(key="native_error_type", actual=type(cause).__name__),
    )
    issue = SimIssue(
        code=code,
        severity="error",
        stage="result.query",
        message="The requested motion result data is unavailable or invalid.",
        object_ids=object_ids,
        evidence=evidence,
        suggested_actions=(
            "Use an ID present in the available_ids evidence and a time within the recorded motion range.",
        ),
    )
    return KinCheckError(
        code=code,
        report=DiagnosticReport(
            issues=(issue,),
            operation=operation,
            status="failed",
        ),
        operation=operation,
    )


def read_joint_state(
    *, motion_result: MotionResult, joint_id: str, time_s: float
) -> JointState:
    try:
        trajectory = _find_joint(motion_result=motion_result, joint_id=joint_id)
        left, right, weight = _bracket(times=trajectory.times_s, time_s=time_s)
        return JointState(
            joint_id=joint_id,
            time_s=float(time_s),
            position=_lerp(trajectory.positions[left], trajectory.positions[right], weight),
            velocity=_lerp(trajectory.velocities[left], trajectory.velocities[right], weight),
            acceleration=_lerp(
                trajectory.accelerations[left], trajectory.accelerations[right], weight
            ),
        )
    except (AttributeError, KeyError, TypeError, ValueError) as cause:
        raise _result_query_error(
            cause=cause,
            operation="read_joint_state",
            requested_id=joint_id if isinstance(joint_id, str) else None,
            available_ids=_available_ids(motion_result=motion_result, kind="joint"),
            code="KINCHECK-RESULT-TRAJECTORY-MISSING",
        ) from cause


def _state_from_trajectory(*, trajectory: Trajectory, time_s: float) -> ComponentState:
    left, right, weight = _bracket(times=trajectory.times_s, time_s=time_s)

    def interpolate_optional(values: tuple[Vector3, ...] | None) -> Vector3 | None:
        if values is None:
            return None
        return _lerp_vector(values[left], values[right], weight)

    return ComponentState(
        component_id=trajectory.component_id,
        time_s=float(time_s),
        pose=_lerp_pose(trajectory.poses[left], trajectory.poses[right], weight),
        linear_velocity_m_s=interpolate_optional(trajectory.linear_velocities_m_s),
        angular_velocity_rad_s=interpolate_optional(trajectory.angular_velocities_rad_s),
        linear_acceleration_m_s2=interpolate_optional(
            trajectory.linear_accelerations_m_s2
        ),
        angular_acceleration_rad_s2=interpolate_optional(
            trajectory.angular_accelerations_rad_s2
        ),
    )


def read_component_pose(
    *, motion_result: MotionResult, component_id: str, time_s: float
) -> Pose:
    return read_component_state(
        motion_result=motion_result, component_id=component_id, time_s=time_s
    ).pose


def read_component_state(
    *, motion_result: MotionResult, component_id: str, time_s: float
) -> ComponentState:
    """Read a Component pose and its available world-frame spatial motion."""

    try:
        trajectory = _find_trajectory(
            motion_result=motion_result, component_id=component_id, connector_id=None
        )
        return _state_from_trajectory(trajectory=trajectory, time_s=time_s)
    except (AttributeError, KeyError, TypeError, ValueError) as cause:
        raise _result_query_error(
            cause=cause,
            operation="read_component_state",
            requested_id=component_id if isinstance(component_id, str) else None,
            available_ids=_available_ids(motion_result=motion_result, kind="component"),
            code="KINCHECK-RESULT-TRAJECTORY-MISSING",
        ) from cause


def read_connector_state(
    *,
    motion_result: MotionResult,
    component_id: str,
    connector_id: str,
    time_s: float,
) -> ConnectorState:
    try:
        trajectory = _find_trajectory(
            motion_result=motion_result,
            component_id=component_id,
            connector_id=connector_id,
        )
        state = _state_from_trajectory(trajectory=trajectory, time_s=time_s)
        return ConnectorState(
            component_id=component_id,
            connector_id=connector_id,
            time_s=state.time_s,
            pose=state.pose,
            linear_velocity_m_s=state.linear_velocity_m_s,
            angular_velocity_rad_s=state.angular_velocity_rad_s,
            linear_acceleration_m_s2=state.linear_acceleration_m_s2,
            angular_acceleration_rad_s2=state.angular_acceleration_rad_s2,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as cause:
        label = (
            f"{component_id}/{connector_id}"
            if isinstance(component_id, str) and isinstance(connector_id, str)
            else None
        )
        raise _result_query_error(
            cause=cause,
            operation="read_connector_state",
            requested_id=label,
            available_ids=_available_ids(motion_result=motion_result, kind="connector"),
            code="KINCHECK-RESULT-TRAJECTORY-MISSING",
        ) from cause


def read_trajectory(
    *, motion_result: MotionResult, component_id: str, connector_id: str | None = None
) -> Trajectory:
    try:
        return _find_trajectory(
            motion_result=motion_result,
            component_id=component_id,
            connector_id=connector_id,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as cause:
        label = (
            component_id
            if connector_id is None and isinstance(component_id, str)
            else f"{component_id}/{connector_id}"
        )
        raise _result_query_error(
            cause=cause,
            operation="read_trajectory",
            requested_id=label,
            available_ids=_available_ids(
                motion_result=motion_result,
                kind="component" if connector_id is None else "connector",
            ),
            code="KINCHECK-RESULT-TRAJECTORY-MISSING",
        ) from cause


def list_constraint_residuals(
    *, motion_result: MotionResult, constraint_id: str | None = None
) -> tuple[ConstraintResidual, ...]:
    try:
        if constraint_id is not None:
            _require_id(constraint_id, "constraint_id")
        return tuple(
            item
            for item in motion_result.constraint_residuals
            if constraint_id is None or item.constraint_id == constraint_id
        )
    except (AttributeError, TypeError, ValueError) as cause:
        raise _result_query_error(
            cause=cause,
            operation="list_constraint_residuals",
            requested_id=constraint_id if isinstance(constraint_id, str) else None,
            available_ids=_available_ids(motion_result=motion_result, kind="constraint"),
        ) from cause


def list_constraint_equation_residuals(
    *, motion_result: MotionResult, constraint_id: str | None = None
) -> tuple[ConstraintEquationResidual, ...]:
    try:
        if constraint_id is not None:
            _require_id(constraint_id, "constraint_id")
        return tuple(
            item
            for item in motion_result.constraint_equation_residuals
            if constraint_id is None or item.constraint_id == constraint_id
        )
    except (AttributeError, TypeError, ValueError) as cause:
        raise _result_query_error(
            cause=cause,
            operation="list_constraint_equation_residuals",
            requested_id=constraint_id if isinstance(constraint_id, str) else None,
            available_ids=tuple(
                item.constraint_id for item in motion_result.constraint_equation_residuals
            ),
        ) from cause


def list_limit_events(
    *, motion_result: MotionResult, joint_id: str | None = None
) -> tuple[LimitEvent, ...]:
    try:
        if joint_id is not None:
            _require_id(joint_id, "joint_id")
        return tuple(
            item
            for item in motion_result.limit_events
            if joint_id is None or item.joint_id == joint_id
        )
    except (AttributeError, TypeError, ValueError) as cause:
        raise _result_query_error(
            cause=cause,
            operation="list_limit_events",
            requested_id=joint_id if isinstance(joint_id, str) else None,
            available_ids=_available_ids(motion_result=motion_result, kind="limit_joint"),
        ) from cause


def list_interference_events(
    *, interference_result: InterferenceResult
) -> tuple[InterferenceEvent, ...]:
    if not isinstance(interference_result, InterferenceResult):
        cause = TypeError("interference_result must be an InterferenceResult")
        raise _result_query_error(
            cause=cause,
            operation="list_interference_events",
        ) from cause
    return interference_result.events


def summarize_motion(*, motion_result: MotionResult) -> MotionSummary:
    extrema = tuple(
        JointExtrema(
            joint_id=item.joint_id,
            minimum_position=min(item.positions),
            maximum_position=max(item.positions),
            maximum_absolute_velocity=max(abs(value) for value in item.velocities),
            maximum_absolute_acceleration=max(abs(value) for value in item.accelerations),
        )
        for item in motion_result.joint_trajectories
    )
    return MotionSummary(
        status=motion_result.status,
        duration_s=motion_result.end_time_s - motion_result.start_time_s,
        sample_count=len(motion_result.sample_times_s),
        joint_extrema=extrema,
        maximum_position_residual_m=max(
            (item.position_residual_m for item in motion_result.constraint_residuals),
            default=0.0,
        ),
        maximum_orientation_residual_rad=max(
            (item.orientation_residual_rad for item in motion_result.constraint_residuals),
            default=0.0,
        ),
        limit_event_count=len(motion_result.limit_events),
        warning_count=sum(item.severity == "warning" for item in motion_result.issues),
    )


def write_motion_result(*, motion_result: MotionResult, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(motion_result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "ComponentState",
    "ConnectorState",
    "ConstraintResidual",
    "ConstraintEquationResidual",
    "ConstraintEquationType",
    "ConstraintEquationUnit",
    "Direction",
    "InterferenceEvent",
    "InterferenceResult",
    "IntegrationSample",
    "DriverTarget",
    "DriverTrajectory",
    "JointExtrema",
    "JointState",
    "JointTrajectory",
    "LimitEvent",
    "MotionResult",
    "MotionStatus",
    "MotionSummary",
    "Trajectory",
    "TransmissionRatioCheck",
    "list_constraint_residuals",
    "list_constraint_equation_residuals",
    "list_interference_events",
    "list_limit_events",
    "read_component_pose",
    "read_component_state",
    "read_connector_state",
    "read_joint_state",
    "read_trajectory",
    "summarize_motion",
    "write_motion_result",
]
