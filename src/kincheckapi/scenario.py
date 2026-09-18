"""Immutable, explicit kinematic scenarios for KinCheckAPI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .assembly import AssemblyModel, JointType
from .diagnostics import DiagnosticReport, Evidence, SimIssue, ValidationResult
from .errors import ScenarioValidationError
from .motion_contracts import CoordinatedMotionProfile, PeriodicProfile, PoseTrajectory


class Interpolation(str, Enum):
    STEP = "step"
    LINEAR = "linear"


class ProfileBoundary(str, Enum):
    HOLD = "hold"
    ZERO = "zero"
    ERROR = "error"


class ComponentResultScope(str, Enum):
    """Which component world-pose trajectories a scenario records."""

    REQUESTED = "requested"
    ALL = "all"


@dataclass(frozen=True, slots=True, kw_only=True)
class ProfilePoint:
    time_s: float
    value: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.time_s) or self.time_s < 0.0:
            raise ValueError("Profile point time_s must be finite and non-negative")
        if not math.isfinite(self.value):
            raise ValueError("Profile point value must be finite")


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionProfile:
    points: tuple[ProfilePoint, ...]
    interpolation: Interpolation | str = Interpolation.LINEAR

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "interpolation", Interpolation(self.interpolation))
        if not self.points:
            raise ValueError("A motion profile must contain at least one point")
        times = tuple(point.time_s for point in self.points)
        if any(current <= previous for previous, current in zip(times, times[1:])):
            raise ValueError("Motion profile times must be strictly increasing")


# The concise alias is useful at the public API boundary.
Profile = MotionProfile


@dataclass(frozen=True, slots=True, kw_only=True)
class JointValue:
    joint_id: str
    value: float


@dataclass(frozen=True, slots=True, kw_only=True)
class JointLock:
    joint_id: str
    position_rad_or_m: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PositionDriver:
    joint_id: str
    profile: MotionProfile


@dataclass(frozen=True, slots=True, kw_only=True)
class SpeedDriver:
    joint_id: str
    profile: MotionProfile
    active_interval_s: tuple[float, float] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionSegment:
    """One non-overlapping interval in a joint motion contract."""
    start_time_s: float
    end_time_s: float
    mode: str
    value: float
    interpolation: Interpolation | str = Interpolation.STEP

    def __post_init__(self) -> None:
        start, end = float(self.start_time_s), float(self.end_time_s)
        if not (math.isfinite(start) and math.isfinite(end) and 0.0 <= start < end):
            raise ValueError("MotionSegment requires 0 <= start_time_s < end_time_s")
        mode = str(self.mode).lower()
        if mode not in {"position", "speed"}:
            raise ValueError("MotionSegment.mode must be 'position' or 'speed'")
        value = float(self.value)
        if not math.isfinite(value):
            raise ValueError("MotionSegment.value must be finite")
        object.__setattr__(self, "start_time_s", start)
        object.__setattr__(self, "end_time_s", end)
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "interpolation", Interpolation(self.interpolation))


@dataclass(frozen=True, slots=True, kw_only=True)
class JointResultRequest:
    joint_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ComponentResultRequest:
    component_id: str
    connector_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Scenario:
    """A reusable kinematic condition bound to exactly one assembly definition."""

    scenario_id: str
    assembly: AssemblyModel = field(repr=False, compare=False)
    assembly_id: str = ""
    initial_joint_positions: tuple[JointValue, ...] = ()
    initial_joint_velocities: tuple[JointValue, ...] = ()
    joint_home_positions: tuple[JointValue, ...] = ()
    locked_joints: tuple[JointLock, ...] = ()
    disabled_constraint_ids: tuple[str, ...] = ()
    position_drivers: tuple[PositionDriver, ...] = ()
    speed_drivers: tuple[SpeedDriver, ...] = ()
    duration_s: float | None = None
    sample_period_s: float | None = None
    joint_result_requests: tuple[JointResultRequest, ...] = ()
    component_result_requests: tuple[ComponentResultRequest, ...] = ()
    component_result_scope: ComponentResultScope | str = ComponentResultScope.REQUESTED
    capture_integration_steps: bool = False
    integration_component_ids: tuple[str, ...] | None = None
    initial_state_source: str = "explicit"
    profile_boundary: ProfileBoundary | str = ProfileBoundary.HOLD
    pose_trajectory_targets: tuple[PoseTrajectory, ...] = ()
    coordinated_profiles: tuple[CoordinatedMotionProfile, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be a non-empty string")
        if not isinstance(self.assembly, AssemblyModel):
            raise TypeError("assembly must be an AssemblyModel")
        if self.assembly_id and self.assembly_id != self.assembly.assembly_id:
            raise ValueError("assembly_id must match the bound assembly")
        object.__setattr__(self, "assembly_id", self.assembly.assembly_id)
        if self.initial_state_source not in {"explicit", "home", "default_zero"}:
            raise ValueError("initial_state_source must be explicit, home, or default_zero")
        object.__setattr__(self, "profile_boundary", ProfileBoundary(self.profile_boundary))
        if not isinstance(self.capture_integration_steps, bool):
            raise TypeError("capture_integration_steps must be a boolean")
        if self.integration_component_ids is not None:
            component_ids = tuple(str(item) for item in self.integration_component_ids)
            if not component_ids or len(set(component_ids)) != len(component_ids) or any(not item for item in component_ids):
                raise ValueError("integration_component_ids must contain unique, non-empty Component IDs")
            known = {item.component_id for item in self.assembly.components}
            if any(item not in known for item in component_ids):
                raise ValueError("integration_component_ids references an unknown Component")
            object.__setattr__(self, "integration_component_ids", component_ids)
        object.__setattr__(
            self,
            "component_result_scope",
            ComponentResultScope(self.component_result_scope),
        )
        for name in (
            "initial_joint_positions",
            "initial_joint_velocities",
            "joint_home_positions",
            "locked_joints",
            "disabled_constraint_ids",
            "position_drivers",
            "speed_drivers",
            "joint_result_requests",
            "component_result_requests",
            "pose_trajectory_targets",
            "coordinated_profiles",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))


def create_scenario(*, scenario_id: str, assembly: AssemblyModel) -> Scenario:
    """Create an empty scenario referencing an immutable assembly model."""

    try:
        return Scenario(scenario_id=scenario_id, assembly=assembly)
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-CREATE-FAILED",
            message="The scenario could not be created from the supplied inputs.",
            object_ids=(str(scenario_id),),
            cause=cause,
        )


def _set_joint_value(
    *, scenario: Scenario, field_name: str, joint_id: str, value: float
) -> Scenario:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-JOINT-VALUE-INVALID",
            message="Joint state values must be numeric SI quantities.",
            object_ids=(scenario.scenario_id, joint_id),
            cause=cause,
        )
    entries = tuple(item for item in getattr(scenario, field_name) if item.joint_id != joint_id)
    return replace(
        scenario,
        **{field_name: (*entries, JointValue(joint_id=joint_id, value=numeric_value))},
    )


def set_initial_joint_position(
    *, scenario: Scenario, joint_id: str, position_rad_or_m: float
) -> Scenario:
    return _set_joint_value(
        scenario=scenario,
        field_name="initial_joint_positions",
        joint_id=joint_id,
        value=position_rad_or_m,
    )


def set_initial_joint_velocity(
    *, scenario: Scenario, joint_id: str, velocity_rad_s_or_m_s: float
) -> Scenario:
    return _set_joint_value(
        scenario=scenario,
        field_name="initial_joint_velocities",
        joint_id=joint_id,
        value=velocity_rad_s_or_m_s,
    )


def set_joint_home_position(
    *, scenario: Scenario, joint_id: str, position_rad_or_m: float
) -> Scenario:
    return _set_joint_value(
        scenario=scenario,
        field_name="joint_home_positions",
        joint_id=joint_id,
        value=position_rad_or_m,
    )


def set_initial_state_from_home(*, scenario: Scenario) -> Scenario:
    """Use declared home positions as the solver's initial state."""
    return replace(scenario, initial_joint_positions=(), initial_state_source="home")


def reset_to_home(*, scenario: Scenario) -> Scenario:
    return set_initial_state_from_home(scenario=scenario)


def lock_joint(
    *, scenario: Scenario, joint_id: str, position_rad_or_m: float | None = None
) -> Scenario:
    locks = tuple(item for item in scenario.locked_joints if item.joint_id != joint_id)
    try:
        value = None if position_rad_or_m is None else float(position_rad_or_m)
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-LOCK-POSITION-INVALID",
            message="Joint lock position must be a numeric SI quantity.",
            object_ids=(scenario.scenario_id, joint_id),
            cause=cause,
        )
    return replace(
        scenario,
        locked_joints=(
            *locks,
            JointLock(joint_id=joint_id, position_rad_or_m=value),
        ),
    )


def disable_constraint(*, scenario: Scenario, constraint_id: str) -> Scenario:
    if constraint_id in scenario.disabled_constraint_ids:
        return scenario
    return replace(
        scenario,
        disabled_constraint_ids=(*scenario.disabled_constraint_ids, constraint_id),
    )


def _coerce_profile(*, profile: MotionProfile | Mapping[str, Any] | Sequence[Any]) -> MotionProfile:
    if isinstance(profile, MotionProfile):
        return profile
    if isinstance(profile, Mapping):
        points = profile.get("points", ())
        interpolation = profile.get("interpolation", Interpolation.LINEAR)
    else:
        points = profile
        interpolation = Interpolation.LINEAR
    normalized: list[ProfilePoint] = []
    for point in points:
        if isinstance(point, ProfilePoint):
            normalized.append(point)
        elif isinstance(point, Mapping):
            normalized.append(ProfilePoint(time_s=float(point["time_s"]), value=float(point["value"])))
        else:
            time_s, value = point
            normalized.append(ProfilePoint(time_s=float(time_s), value=float(value)))
    return MotionProfile(points=tuple(normalized), interpolation=interpolation)


def add_joint_position_driver(
    *, scenario: Scenario, joint_id: str, profile: MotionProfile | Mapping[str, Any] | Sequence[Any]
) -> Scenario:
    try:
        normalized = _coerce_profile(profile=profile)
    except (KeyError, TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-PROFILE-INVALID",
            message="The position profile is invalid.",
            object_ids=(scenario.scenario_id, joint_id),
            cause=cause,
        )
    driver = PositionDriver(joint_id=joint_id, profile=normalized)
    return replace(scenario, position_drivers=(*scenario.position_drivers, driver))


def add_joint_speed_driver(
    *,
    scenario: Scenario,
    joint_id: str,
    speed_rad_s_or_m_s: float,
    start_time_s: float,
    end_time_s: float,
) -> Scenario:
    try:
        start_time = float(start_time_s)
        end_time = float(end_time_s)
        speed = float(speed_rad_s_or_m_s)
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-DRIVER-VALUE-INVALID",
            message="Speed and driver times must be numeric SI quantities.",
            object_ids=(scenario.scenario_id, joint_id),
            cause=cause,
        )
    if not math.isfinite(speed):
        _raise_validation(
            code="KINCHECK-SCENARIO-DRIVER-VALUE-INVALID",
            message="A constant speed driver requires a finite speed.",
            object_ids=(scenario.scenario_id, joint_id),
        )
    if (
        not math.isfinite(start_time)
        or not math.isfinite(end_time)
        or start_time < 0.0
        or end_time <= start_time
    ):
        _raise_validation(
            code="KINCHECK-SCENARIO-DRIVER-TIME-INVALID",
            message="A constant speed driver requires 0 <= start_time_s < end_time_s.",
            object_ids=(scenario.scenario_id, joint_id),
        )
    profile = MotionProfile(
        points=(
            ProfilePoint(time_s=start_time, value=speed),
            ProfilePoint(time_s=end_time, value=speed),
        ),
        interpolation=Interpolation.STEP,
    )
    return replace(
        scenario,
        speed_drivers=(
            *scenario.speed_drivers,
            SpeedDriver(
                joint_id=joint_id,
                profile=profile,
                active_interval_s=(start_time, end_time),
            ),
        ),
    )


def add_joint_speed_profile(
    *, scenario: Scenario, joint_id: str, profile: MotionProfile | Mapping[str, Any] | Sequence[Any]
) -> Scenario:
    try:
        normalized = _coerce_profile(profile=profile)
    except (KeyError, TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-PROFILE-INVALID",
            message="The speed profile is invalid.",
            object_ids=(scenario.scenario_id, joint_id),
            cause=cause,
        )
    driver = SpeedDriver(joint_id=joint_id, profile=normalized)
    return replace(scenario, speed_drivers=(*scenario.speed_drivers, driver))


def add_joint_motion_segments(
    *, scenario: Scenario, joint_id: str, segments: Sequence[MotionSegment | Mapping[str, Any]]
) -> Scenario:
    """Add an ordered piecewise position or speed driver for one joint."""
    try:
        normalized = tuple(
            item if isinstance(item, MotionSegment) else MotionSegment(**dict(item))
            for item in segments
        )
        if not normalized:
            raise ValueError("segments must contain at least one MotionSegment")
        ordered = tuple(sorted(normalized, key=lambda item: item.start_time_s))
        if any(a.end_time_s > b.start_time_s for a, b in zip(ordered, ordered[1:])):
            raise ValueError("Motion segments for one joint must not overlap")
        if any(abs(a.end_time_s - b.start_time_s) > 1e-12 for a, b in zip(ordered, ordered[1:])):
            raise ValueError("Motion segments for one joint must be contiguous; use an explicit zero or hold segment for a gap")
        if len({item.mode for item in ordered}) != 1:
            raise ValueError("A joint motion segment list must use one driver mode")
        if len({item.interpolation for item in ordered}) != 1:
            raise ValueError("Motion segments for one joint must use one interpolation mode")
        mode = ordered[0].mode
        point_values: list[tuple[float, float]] = [(ordered[0].start_time_s, ordered[0].value)]
        for segment in ordered:
            if point_values[-1][0] == segment.start_time_s:
                point_values[-1] = (segment.start_time_s, segment.value)
            else:
                point_values.append((segment.start_time_s, segment.value))
            point_values.append((segment.end_time_s, segment.value))
        points = tuple(ProfilePoint(time_s=t, value=v) for t, v in point_values)
        profile = MotionProfile(points=points, interpolation=ordered[0].interpolation)
        if mode == "position":
            return replace(scenario, position_drivers=tuple(d for d in scenario.position_drivers if d.joint_id != joint_id) + (PositionDriver(joint_id=joint_id, profile=profile),))
        return replace(scenario, speed_drivers=tuple(d for d in scenario.speed_drivers if d.joint_id != joint_id) + (SpeedDriver(joint_id=joint_id, profile=profile, active_interval_s=(ordered[0].start_time_s, ordered[-1].end_time_s)),))
    except (TypeError, ValueError, KeyError) as cause:
        _raise_validation(code="KINCHECK-SCENARIO-MOTION-SEGMENTS-INVALID", message="Joint motion segments are invalid.", object_ids=(scenario.scenario_id, joint_id), cause=cause)


def replace_joint_driver(*, scenario: Scenario, joint_id: str, driver: PositionDriver | SpeedDriver) -> Scenario:
    if driver.joint_id != joint_id:
        raise ValueError("driver.joint_id must match joint_id")
    scenario = clear_joint_drivers(scenario=scenario, joint_id=joint_id)
    return replace(scenario, position_drivers=(*scenario.position_drivers, driver)) if isinstance(driver, PositionDriver) else replace(scenario, speed_drivers=(*scenario.speed_drivers, driver))


def remove_joint_driver(*, scenario: Scenario, joint_id: str) -> Scenario:
    return clear_joint_drivers(scenario=scenario, joint_id=joint_id)


def clear_joint_drivers(*, scenario: Scenario, joint_id: str | None = None) -> Scenario:
    if joint_id is None:
        return replace(scenario, position_drivers=(), speed_drivers=())
    return replace(scenario, position_drivers=tuple(d for d in scenario.position_drivers if d.joint_id != joint_id), speed_drivers=tuple(d for d in scenario.speed_drivers if d.joint_id != joint_id))


def set_run_duration(*, scenario: Scenario, duration_s: float) -> Scenario:
    try:
        return replace(scenario, duration_s=float(duration_s))
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-DURATION-INVALID",
            message="duration_s must be a numeric SI quantity.",
            object_ids=(scenario.scenario_id,),
            cause=cause,
        )


def set_sample_period(*, scenario: Scenario, period_s: float) -> Scenario:
    try:
        return replace(scenario, sample_period_s=float(period_s))
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-SAMPLE-PERIOD-INVALID",
            message="period_s must be a numeric SI quantity.",
            object_ids=(scenario.scenario_id,),
            cause=cause,
        )


def set_profile_boundary(*, scenario: Scenario, behavior: ProfileBoundary | str) -> Scenario:
    try:
        normalized = ProfileBoundary(behavior)
    except (TypeError, ValueError) as cause:
        _raise_validation(code="KINCHECK-SCENARIO-PROFILE-BOUNDARY-INVALID", message="Profile boundary must be 'hold', 'zero', or 'error'.", object_ids=(scenario.scenario_id,), cause=cause)
    return replace(scenario, profile_boundary=normalized)


def add_periodic_joint_driver(
    *, scenario: Scenario, joint_id: str, profile: PeriodicProfile,
) -> Scenario:
    """Sample a periodic scalar target into an explicit position profile."""
    if scenario.duration_s is None or scenario.sample_period_s is None:
        _raise_validation(
            code="KINCHECK-SCENARIO-PERIODIC-WINDOW-MISSING",
            message="A duration and sample period are required before adding a periodic driver.",
            object_ids=(scenario.scenario_id, joint_id),
        )
    try:
        motion_profile = profile.to_motion_profile(
            start_time_s=0.0,
            end_time_s=float(scenario.duration_s),
            sample_period_s=float(scenario.sample_period_s),
        )
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-PERIODIC-PROFILE-INVALID",
            message="The periodic profile cannot be sampled for this Scenario.",
            object_ids=(scenario.scenario_id, joint_id),
            cause=cause,
        )
    return add_joint_position_driver(
        scenario=scenario, joint_id=joint_id, profile=motion_profile
    )


def add_coordinated_motion_profile(
    *, scenario: Scenario, profile: CoordinatedMotionProfile,
) -> Scenario:
    """Convert one shared-time scalar target into one position driver per axis."""
    if not isinstance(profile, CoordinatedMotionProfile):
        _raise_validation(
            code="KINCHECK-SCENARIO-COORDINATED-PROFILE-INVALID",
            message="profile must be a CoordinatedMotionProfile.",
            object_ids=(scenario.scenario_id,),
        )
    if scenario.duration_s is not None and profile.times_s[-1] > scenario.duration_s:
        _raise_validation(
            code="KINCHECK-SCENARIO-COORDINATED-PROFILE-OUTSIDE-RANGE",
            message="A coordinated profile extends past the Scenario duration.",
            object_ids=(scenario.scenario_id,),
        )
    result = clear_joint_drivers(scenario=scenario)
    for joint_id, values in profile.axes.items():
        result = add_joint_position_driver(
            scenario=result,
            joint_id=joint_id,
            profile=MotionProfile(
                points=tuple(
                    ProfilePoint(time_s=time_s, value=value)
                    for time_s, value in zip(profile.times_s, values)
                ),
            ),
        )
    return replace(
        result,
        coordinated_profiles=(*result.coordinated_profiles, profile),
    )


def add_pose_trajectory_target(
    *, scenario: Scenario, target: PoseTrajectory,
) -> Scenario:
    """Record a Cartesian acceptance target; solving it requires a supported driver."""
    if not isinstance(target, PoseTrajectory):
        _raise_validation(
            code="KINCHECK-SCENARIO-POSE-TRAJECTORY-INVALID",
            message="target must be a PoseTrajectory.",
            object_ids=(scenario.scenario_id,),
        )
    return replace(
        scenario,
        pose_trajectory_targets=(*scenario.pose_trajectory_targets, target),
    )


def add_component_pose_driver(*, scenario: Scenario, target: PoseTrajectory) -> Scenario:
    """Explicitly reject Cartesian driving until a 6D backend is available."""
    from .errors import BackendCapabilityError
    issue = _issue(
        code="KINCHECK-SCENARIO-CAPABILITY-UNSUPPORTED",
        message="Cartesian PoseTrajectory drivers are not implemented by the scalar backend.",
        object_ids=(scenario.scenario_id, target.target.component_id),
        action="Use a scalar Joint profile and check_pose_trajectory, or provide a 6D backend.",
    )
    raise BackendCapabilityError(
        code="KINCHECK-SCENARIO-CAPABILITY-UNSUPPORTED",
        message=issue.message,
        report=DiagnosticReport(
            issues=(issue,), operation="add_component_pose_driver", status="capability_failed"
        ),
        object_ids=issue.object_ids,
        operation="add_component_pose_driver",
        missing_capabilities=("cartesian_pose_driver",),
    )


def request_joint_result(*, scenario: Scenario, joint_id: str) -> Scenario:
    if any(item.joint_id == joint_id for item in scenario.joint_result_requests):
        return scenario
    return replace(
        scenario,
        joint_result_requests=(
            *scenario.joint_result_requests,
            JointResultRequest(joint_id=joint_id),
        ),
    )


def request_component_result(
    *, scenario: Scenario, component_id: str, connector_id: str | None = None
) -> Scenario:
    request = ComponentResultRequest(component_id=component_id, connector_id=connector_id)
    if request in scenario.component_result_requests:
        return scenario
    return replace(
        scenario,
        component_result_requests=(*scenario.component_result_requests, request),
    )


def set_component_result_scope(
    *, scenario: Scenario, scope: ComponentResultScope | str
) -> Scenario:
    """Select requested-only or complete component pose trajectories.

    ``requested`` preserves the historical behavior: an empty request list
    records every component, while an explicit list records only those IDs.
    ``all`` always records every component, including fixed hardware members.
    """

    try:
        normalized = ComponentResultScope(scope)
    except (TypeError, ValueError) as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-COMPONENT-RESULT-SCOPE-INVALID",
            message="Component result scope must be 'requested' or 'all'.",
            object_ids=(scenario.scenario_id, str(scope)),
            cause=cause,
        )
    return replace(scenario, component_result_scope=normalized)


def set_capture_integration_steps(
    *, scenario: Scenario, enabled: bool, component_ids: Sequence[str] | None = None
) -> Scenario:
    """Opt into retaining every internal physics backend integration-step pose.

    The default is off to keep long MotionResults compact.  Clearance checks
    using ``sampling_scope='solver_steps'`` require this explicit capture.
    """
    if not isinstance(enabled, bool):
        _raise_validation(
            code="KINCHECK-SCENARIO-CAPTURE-INVALID",
            message="enabled must be a boolean.",
            object_ids=(scenario.scenario_id,),
        )
    normalized = None if component_ids is None or not enabled else tuple(dict.fromkeys(str(item) for item in component_ids))
    if enabled and component_ids is not None and not normalized:
        _raise_validation(
            code="KINCHECK-SCENARIO-CAPTURE-INVALID",
            message="component_ids cannot be empty when physics backend integration capture is enabled.",
            object_ids=(scenario.scenario_id,),
        )
    known = {item.component_id for item in scenario.assembly.components}
    unknown = tuple(item for item in (normalized or ()) if item not in known)
    if unknown:
        _raise_validation(
            code="KINCHECK-SCENARIO-COMPONENT-NOT-FOUND",
            message="integration capture references unknown components.",
            object_ids=(scenario.scenario_id, *unknown),
        )
    return replace(scenario, capture_integration_steps=enabled, integration_component_ids=normalized)


def _issue(
    *,
    code: str,
    message: str,
    object_ids: Iterable[str] = (),
    evidence: Iterable[Evidence] = (),
    action: str,
) -> SimIssue:
    source_paths: list[str] = []
    return SimIssue(
        code=code,
        severity="error",
        stage="scenario",
        message=message,
        object_ids=tuple(object_ids),
        source_paths=tuple(source_paths),
        evidence=tuple(evidence),
        suggested_actions=(action,),
    )


def validate_scenario(*, scenario: Scenario) -> ValidationResult:
    """Aggregate time, reference, limit, and driver conflict errors."""

    issues: list[SimIssue] = []
    for joint in scenario.assembly.joints:
        if joint.joint_type not in {JointType.FIXED, JointType.REVOLUTE, JointType.PRISMATIC}:
            issues.append(_issue(
                code="KINCHECK-SCENARIO-JOINT-CAPABILITY-UNSUPPORTED",
                message="The selected backend supports only fixed, revolute, and prismatic scalar joints.",
                object_ids=(scenario.scenario_id, joint.joint_id),
                evidence=(Evidence(key="joint_type", actual=joint.joint_type.value, expected=("fixed", "revolute", "prismatic")),),
                action="Use a supported scalar joint or provide a backend with the requested multi-DOF capability.",
            ))
    if scenario.duration_s is None or not math.isfinite(scenario.duration_s) or scenario.duration_s <= 0.0:
        issues.append(
            _issue(
                code="KINCHECK-SCENARIO-DURATION-INVALID",
                message="Scenario duration must be finite and greater than zero.",
                object_ids=(scenario.scenario_id,),
                evidence=(Evidence(key="duration_s", actual=scenario.duration_s, expected="> 0", unit="s"),),
                action="Call set_run_duration() with a positive duration_s.",
            )
        )
    if (
        scenario.sample_period_s is None
        or not math.isfinite(scenario.sample_period_s)
        or scenario.sample_period_s <= 0.0
    ):
        issues.append(
            _issue(
                code="KINCHECK-SCENARIO-SAMPLE-PERIOD-INVALID",
                message="Scenario sample period must be finite and greater than zero.",
                object_ids=(scenario.scenario_id,),
                evidence=(Evidence(key="sample_period_s", actual=scenario.sample_period_s, expected="> 0", unit="s"),),
                action="Call set_sample_period() with a positive period_s.",
            )
        )
    elif scenario.duration_s is not None and scenario.duration_s > 0.0 and scenario.sample_period_s > scenario.duration_s:
        issues.append(
            _issue(
                code="KINCHECK-SCENARIO-SAMPLE-PERIOD-TOO-LARGE",
                message="Sample period cannot exceed the run duration.",
                object_ids=(scenario.scenario_id,),
                evidence=(Evidence(key="sample_period_s", actual=scenario.sample_period_s, expected=f"<= {scenario.duration_s}", unit="s"),),
                action="Reduce period_s or increase duration_s.",
            )
        )

    def require_joint(joint_id: str, owner: str) -> Any:
        joint = scenario.assembly.get_joint(joint_id=joint_id)
        if joint is None:
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-JOINT-NOT-FOUND",
                    message=f"{owner} references an unknown joint.",
                    object_ids=(scenario.scenario_id, joint_id),
                    action="Use a Joint ID present in the bound assembly.",
                )
            )
        return joint

    values = (
        *scenario.initial_joint_positions,
        *scenario.initial_joint_velocities,
        *scenario.joint_home_positions,
    )
    for value in values:
        require_joint(value.joint_id, "Joint state")
        if not math.isfinite(value.value):
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-JOINT-VALUE-INVALID",
                    message="Joint state values must be finite.",
                    object_ids=(scenario.scenario_id, value.joint_id),
                    evidence=(Evidence(key="value", actual=value.value, expected="finite"),),
                    action="Replace the value with a finite SI quantity.",
                )
            )
    for lock in scenario.locked_joints:
        require_joint(lock.joint_id, "Joint lock")
        if lock.position_rad_or_m is not None and not math.isfinite(lock.position_rad_or_m):
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-LOCK-POSITION-INVALID",
                    message="A joint lock position must be finite.",
                    object_ids=(scenario.scenario_id, lock.joint_id),
                    action="Provide a finite position or omit it to use the initial position.",
                )
            )
    for request in scenario.joint_result_requests:
        require_joint(request.joint_id, "Joint result request")

    known_constraints = {
        item.constraint_id for item in scenario.assembly.constraints
    } | {item.closure_id for item in scenario.assembly.closures}
    for constraint_id in scenario.disabled_constraint_ids:
        if constraint_id not in known_constraints:
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-CONSTRAINT-NOT-FOUND",
                    message="Disabled constraint is not present in the bound assembly.",
                    object_ids=(scenario.scenario_id, constraint_id),
                    action="Use an explicit Constraint or Closure ID from the assembly.",
                )
            )

    for request in scenario.component_result_requests:
        component = scenario.assembly.get_component(component_id=request.component_id)
        if component is None:
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-COMPONENT-NOT-FOUND",
                    message="Component result request references an unknown component.",
                    object_ids=(scenario.scenario_id, request.component_id),
                    action="Use a Component ID present in the bound assembly.",
                )
            )
        elif request.connector_id is not None and scenario.assembly.get_connector(
            component_id=request.component_id, connector_id=request.connector_id
        ) is None:
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-CONNECTOR-NOT-FOUND",
                    message="Component result request references an unknown Connector.",
                    object_ids=(scenario.scenario_id, request.component_id, request.connector_id),
                    action="Use a Connector ID defined on the component or its Part.",
                )
                )

    for target in scenario.pose_trajectory_targets:
        component = scenario.assembly.get_component(component_id=target.target.component_id)
        if component is None:
            issues.append(_issue(
                code="KINCHECK-SCENARIO-POSE-TARGET-NOT-FOUND",
                message="PoseTrajectory target references an unknown component.",
                object_ids=(scenario.scenario_id, target.target.component_id),
                action="Use a Component ID present in the bound assembly.",
            ))
        elif target.target.connector_id is not None and scenario.assembly.get_connector(
            component_id=target.target.component_id,
            connector_id=target.target.connector_id,
        ) is None:
            issues.append(_issue(
                code="KINCHECK-SCENARIO-POSE-TARGET-NOT-FOUND",
                message="PoseTrajectory target references an unknown connector.",
                object_ids=(scenario.scenario_id, target.target.component_id, target.target.connector_id),
                action="Use a Connector ID defined by the target component or part.",
            ))
        if scenario.duration_s is not None and target.points[-1].time_s > scenario.duration_s:
            issues.append(_issue(
                code="KINCHECK-SCENARIO-POSE-TARGET-OUTSIDE-RANGE",
                message="PoseTrajectory extends past the Scenario duration.",
                object_ids=(scenario.scenario_id, target.target.component_id),
                evidence=(Evidence(key="target_end_time_s", actual=target.points[-1].time_s, expected=f"<= {scenario.duration_s}", unit="s"),),
                action="Trim the pose target or increase duration_s.",
            ))

    driven_joint_ids: dict[str, list[str]] = {}
    for driver_type, drivers in (
        ("position", scenario.position_drivers),
        ("speed", scenario.speed_drivers),
    ):
        for driver in drivers:
            joint = require_joint(driver.joint_id, f"{driver_type.title()} driver")
            driven_joint_ids.setdefault(driver.joint_id, []).append(driver_type)
            if driver.profile.points[0].time_s > 0.0 and scenario.profile_boundary is ProfileBoundary.ERROR:
                issues.append(_issue(
                    code="KINCHECK-SCENARIO-PROFILE-DOES-NOT-START-AT-ZERO",
                    message="A profile with ERROR boundary must start at t=0.",
                    object_ids=(scenario.scenario_id, driver.joint_id),
                    evidence=(Evidence(key="profile_start_time_s", actual=driver.profile.points[0].time_s, expected=0.0, unit="s"),),
                    action="Add a profile point at t=0 or choose hold/zero boundary behavior.",
                ))
            if driver.profile.points[-1].time_s > (scenario.duration_s or 0.0):
                issues.append(
                    _issue(
                        code="KINCHECK-SCENARIO-DRIVER-OUTSIDE-RANGE",
                        message="A driver profile extends past the scenario duration.",
                        object_ids=(scenario.scenario_id, driver.joint_id),
                        evidence=(Evidence(key="profile_end_time_s", actual=driver.profile.points[-1].time_s, expected=f"<= {scenario.duration_s}", unit="s"),),
                        action="Trim the profile or increase duration_s.",
                    )
                )
            if joint is not None and joint.joint_type == JointType.FIXED:
                issues.append(
                    _issue(
                        code="KINCHECK-SCENARIO-FIXED-JOINT-DRIVEN",
                        message="A fixed joint cannot have a motion driver.",
                        object_ids=(scenario.scenario_id, driver.joint_id),
                        action="Remove the driver or use a movable joint.",
                    )
                )
    locked_ids = {lock.joint_id for lock in scenario.locked_joints}
    for joint_id, kinds in driven_joint_ids.items():
        if len(kinds) > 1 or joint_id in locked_ids:
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-DRIVER-CONFLICT",
                    message="A joint cannot be locked or have both position and speed drivers.",
                    object_ids=(scenario.scenario_id, joint_id),
                    evidence=(Evidence(key="driver_kinds", actual=sorted(kinds), expected="exactly one driver and unlocked"),),
                    action="Remove the conflicting lock or driver.",
                )
            )

    positions = {item.joint_id: item.value for item in scenario.initial_joint_positions}
    homes = {item.joint_id: item.value for item in scenario.joint_home_positions}
    if scenario.initial_state_source == "home" and not homes:
        issues.append(_issue(code="KINCHECK-SCENARIO-HOME-EMPTY", message="Home initial state was requested but no home positions are declared.", object_ids=(scenario.scenario_id,), action="Declare at least one joint home position before selecting home initialization."))
    locks = {
        item.joint_id: item.position_rad_or_m
        for item in scenario.locked_joints
        if item.position_rad_or_m is not None
    }
    for lock in scenario.locked_joints:
        if (
            lock.position_rad_or_m is not None
            and lock.joint_id in positions
            and not math.isclose(
                float(lock.position_rad_or_m),
                float(positions[lock.joint_id]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-LOCK-CONFLICT",
                    message="A locked Joint has a different initial position.",
                    object_ids=(scenario.scenario_id, lock.joint_id),
                    evidence=(
                        Evidence(
                            key="lock_position",
                            actual=lock.position_rad_or_m,
                            expected=positions[lock.joint_id],
                            unit="rad_or_m",
                        ),
                    ),
                    action="Use one consistent value for the lock and initial Joint position.",
                )
            )
    for joint_id, value in (*positions.items(), *homes.items(), *locks.items()):
        joint = scenario.assembly.get_joint(joint_id=joint_id)
        if joint is not None and joint.limit is not None and not (joint.limit.lower <= value <= joint.limit.upper):
            issues.append(
                _issue(
                    code="KINCHECK-SCENARIO-JOINT-LIMIT-VIOLATION",
                    message="An initial or home joint position lies outside its assembly limit.",
                    object_ids=(scenario.scenario_id, joint_id),
                    evidence=(Evidence(key="position", actual=value, expected=[joint.limit.lower, joint.limit.upper]),),
                    action="Choose a position inside the explicit joint limits.",
                )
            )
    if scenario.assembly.source_path:
        issues = [
            replace(issue, source_paths=(scenario.assembly.source_path,))
            if not issue.source_paths
            else issue
            for issue in issues
        ]
    return ValidationResult(issues=tuple(issues), operation="validate_scenario")


def _profile_to_dict(profile: MotionProfile) -> dict[str, Any]:
    return {
        "interpolation": profile.interpolation.value,
        "points": [asdict(point) for point in profile.points],
    }


def scenario_to_dict(*, scenario: Scenario) -> dict[str, Any]:
    return {
        "schema_version": "kincheckapi.scenario/1.0",
        "scenario_id": scenario.scenario_id,
        "assembly_id": scenario.assembly_id,
        "initial_joint_positions": [asdict(item) for item in scenario.initial_joint_positions],
        "initial_joint_velocities": [asdict(item) for item in scenario.initial_joint_velocities],
        "joint_home_positions": [asdict(item) for item in scenario.joint_home_positions],
        "locked_joints": [asdict(item) for item in scenario.locked_joints],
        "disabled_constraint_ids": list(scenario.disabled_constraint_ids),
        "position_drivers": [
            {"joint_id": item.joint_id, "profile": _profile_to_dict(item.profile)}
            for item in scenario.position_drivers
        ],
        "speed_drivers": [
            {
                "joint_id": item.joint_id,
                "profile": _profile_to_dict(item.profile),
                "active_interval_s": (
                    list(item.active_interval_s) if item.active_interval_s is not None else None
                ),
            }
            for item in scenario.speed_drivers
        ],
        "duration_s": scenario.duration_s,
        "sample_period_s": scenario.sample_period_s,
        "joint_result_requests": [asdict(item) for item in scenario.joint_result_requests],
        "component_result_requests": [
            asdict(item) for item in scenario.component_result_requests
        ],
        "component_result_scope": scenario.component_result_scope.value,
        "capture_integration_steps": scenario.capture_integration_steps,
        "integration_component_ids": (
            list(scenario.integration_component_ids)
            if scenario.integration_component_ids is not None else None
        ),
        "initial_state_source": scenario.initial_state_source,
        "profile_boundary": scenario.profile_boundary.value,
        "pose_trajectory_targets": [item.to_dict() for item in scenario.pose_trajectory_targets],
        "coordinated_profiles": [item.to_dict() for item in scenario.coordinated_profiles],
    }


def _joint_values(data: Iterable[Mapping[str, Any]]) -> tuple[JointValue, ...]:
    return tuple(JointValue(joint_id=str(item["joint_id"]), value=float(item["value"])) for item in data)


def scenario_from_dict(*, assembly: AssemblyModel, data: Mapping[str, Any]) -> Scenario:
    """Construct a Scenario from parsed JSON without performing strict validation."""

    if data.get("assembly_id") != assembly.assembly_id:
        _raise_validation(
            code="KINCHECK-SCENARIO-ASSEMBLY-MISMATCH",
            message="Scenario assembly_id does not match the supplied assembly.",
            object_ids=(str(data.get("assembly_id")), assembly.assembly_id),
        )
    return Scenario(
        scenario_id=str(data["scenario_id"]),
        assembly=assembly,
        initial_joint_positions=_joint_values(data.get("initial_joint_positions", ())),
        initial_joint_velocities=_joint_values(data.get("initial_joint_velocities", ())),
        joint_home_positions=_joint_values(data.get("joint_home_positions", ())),
        locked_joints=tuple(
            JointLock(
                joint_id=str(item["joint_id"]),
                position_rad_or_m=(
                    None if item.get("position_rad_or_m") is None else float(item["position_rad_or_m"])
                ),
            )
            for item in data.get("locked_joints", ())
        ),
        disabled_constraint_ids=tuple(str(item) for item in data.get("disabled_constraint_ids", ())),
        position_drivers=tuple(
            PositionDriver(joint_id=str(item["joint_id"]), profile=_coerce_profile(profile=item["profile"]))
            for item in data.get("position_drivers", ())
        ),
        speed_drivers=tuple(
            SpeedDriver(
                joint_id=str(item["joint_id"]),
                profile=_coerce_profile(profile=item["profile"]),
                active_interval_s=(
                    tuple(float(value) for value in item["active_interval_s"])
                    if item.get("active_interval_s") is not None
                    else None
                ),
            )
            for item in data.get("speed_drivers", ())
        ),
        duration_s=None if data.get("duration_s") is None else float(data["duration_s"]),
        sample_period_s=(
            None if data.get("sample_period_s") is None else float(data["sample_period_s"])
        ),
        joint_result_requests=tuple(
            JointResultRequest(joint_id=str(item["joint_id"]))
            for item in data.get("joint_result_requests", ())
        ),
        component_result_requests=tuple(
            ComponentResultRequest(
                component_id=str(item["component_id"]), connector_id=item.get("connector_id")
            )
            for item in data.get("component_result_requests", ())
        ),
        component_result_scope=data.get(
            "component_result_scope", ComponentResultScope.REQUESTED.value
        ),
        capture_integration_steps=data.get("capture_integration_steps", False),
        integration_component_ids=(
            None if data.get("integration_component_ids") is None
            else tuple(str(item) for item in data["integration_component_ids"])
        ),
        initial_state_source=str(data.get("initial_state_source", "explicit")),
        profile_boundary=data.get("profile_boundary", ProfileBoundary.HOLD.value),
        pose_trajectory_targets=tuple(
            PoseTrajectory.from_dict(item) for item in data.get("pose_trajectory_targets", ())
        ),
        coordinated_profiles=tuple(
            CoordinatedMotionProfile(
                times_s=tuple(item["times_s"]),
                axes={key: tuple(value) for key, value in item["axes"].items()},
                position_tolerance=float(item.get("position_tolerance", 1e-6)),
            )
            for item in data.get("coordinated_profiles", ())
        ),
    )


def write_scenario(*, scenario: Scenario, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(scenario_to_dict(scenario=scenario), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_scenario(*, assembly: AssemblyModel, path: str | Path) -> Scenario:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        if data.get("schema_version") != "kincheckapi.scenario/1.0":
            _raise_validation(
                code="KINCHECK-SCENARIO-SCHEMA-UNSUPPORTED",
                message=f"Unsupported scenario schema: {data.get('schema_version')!r}.",
                source_paths=(str(source),),
            )
        scenario = scenario_from_dict(assembly=assembly, data=data)
    except ScenarioValidationError:
        raise
    except Exception as cause:
        _raise_validation(
            code="KINCHECK-SCENARIO-READ-FAILED",
            message="The scenario JSON could not be read or reconstructed.",
            source_paths=(str(source),),
            cause=cause,
        )
    validation = validate_scenario(scenario=scenario)
    if not validation.passed:
        raise ScenarioValidationError(
            code="KINCHECK-SCENARIO-VALIDATION-FAILED",
            message="Scenario JSON contains invalid inputs or references.",
            report=_report_from_validation(validation),
            source_paths=(str(source),),
        )
    return scenario


def _report_from_validation(validation: ValidationResult) -> Any:
    from .diagnostics import DiagnosticReport

    return DiagnosticReport(issues=validation.issues)


def _raise_validation(
    *,
    code: str,
    message: str,
    object_ids: tuple[str, ...] = (),
    source_paths: tuple[str, ...] = (),
    cause: BaseException | None = None,
) -> None:
    issue = SimIssue(
        code=code,
        severity="error",
        stage="scenario",
        message=message,
        object_ids=object_ids,
        source_paths=source_paths,
        evidence=(
            (Evidence(key="native_error_type", actual=type(cause).__name__),)
            if cause is not None
            else ()
        ),
        suggested_actions=("Correct the scenario input and retry.",),
    )
    error = ScenarioValidationError(
        code=code,
        message=message,
        report=_report_from_validation(ValidationResult(issues=(issue,))),
        object_ids=object_ids,
        source_paths=source_paths,
    )
    if cause is not None:
        raise error from cause
    raise error


__all__ = [
    "ComponentResultScope",
    "ComponentResultRequest",
    "Interpolation",
    "ProfileBoundary",
    "JointLock",
    "JointResultRequest",
    "JointValue",
    "MotionProfile",
    "MotionSegment",
    "PositionDriver",
    "Profile",
    "ProfilePoint",
    "Scenario",
    "SpeedDriver",
    "add_joint_position_driver",
    "add_joint_speed_driver",
    "add_joint_speed_profile",
    "add_joint_motion_segments",
    "add_periodic_joint_driver",
    "add_coordinated_motion_profile",
    "add_pose_trajectory_target",
    "add_component_pose_driver",
    "create_scenario",
    "disable_constraint",
    "replace_joint_driver",
    "remove_joint_driver",
    "clear_joint_drivers",
    "lock_joint",
    "read_scenario",
    "request_component_result",
    "request_joint_result",
    "scenario_from_dict",
    "scenario_to_dict",
    "set_initial_joint_position",
    "set_initial_joint_velocity",
    "set_initial_state_from_home",
    "reset_to_home",
    "set_component_result_scope",
    "set_capture_integration_steps",
    "set_joint_home_position",
    "set_run_duration",
    "set_sample_period",
    "set_profile_boundary",
    "validate_scenario",
    "write_scenario",
]
