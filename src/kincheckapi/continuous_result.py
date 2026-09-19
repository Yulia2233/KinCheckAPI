"""Contracts and lossless evidence for bounded continuous mesh checking."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Literal, Mapping

from .assembly import _freeze_mapping
from .diagnostics import AgentReadableResult, DiagnosticReport, Evidence, SimIssue, _json_value


def _finite(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, str, bytes)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (result <= 0 if positive else result < 0):
        raise ValueError(f"{name} must be finite and {'positive' if positive else 'non-negative'}")
    return result


def _vector(value: Any) -> tuple[float, float, float]:
    result = tuple(float(v) for v in value)
    if len(result) != 3 or not all(math.isfinite(v) for v in result):
        raise ValueError("vector must contain three finite values")
    return result


@dataclass(frozen=True, slots=True, kw_only=True)
class ContinuousInterferenceOptions:
    """Numerical budgets for a declared piecewise rigid motion model.

    slerp_pose means linear translation and exact shortest-arc SLERP per interval.
    linear_pose supports translation with constant orientation only. None means
    no between-sample model, so no continuous safety verdict is possible.
    max_iterations is the subdivision depth per input interval; max_subdivisions
    and max_queries are global budgets across every pair and input interval.
    """

    time_tolerance_s: float = 1e-5
    distance_tolerance_m: float = 1e-6
    minimum_clearance_m: float = 0.0
    max_iterations: int = 64
    max_subdivisions: int = 4096
    max_queries: int = 100000
    require_velocity_bound: bool = True
    interpolation: Literal["linear_pose", "slerp_pose"] | None = "slerp_pose"
    report_contact_normal: bool = True

    def __post_init__(self) -> None:
        for name in ("time_tolerance_s", "distance_tolerance_m", "minimum_clearance_m"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, positive=name != "minimum_clearance_m"))
        for name in ("max_iterations", "max_subdivisions", "max_queries"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("require_velocity_bound", "report_contact_normal"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be boolean")
        if self.interpolation not in {None, "linear_pose", "slerp_pose"}:
            raise ValueError("interpolation must be slerp_pose, linear_pose, or None")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContinuousContactEvent:
    """First possible entry and observed violation for one explicit component pair.

    earliest_contact_time_s is an upper bound, never an exact impact claim.
    time_interval_s retains the earliest unresolved prefix; toi_tolerance_met
    in evidence records whether the bracket meets the requested precision.
    Geometry and velocities refer to state_time_s. Positive signed distance is
    separation; non-positive FCL contact evidence is not an exact penetration metric.
    Relative velocity is world-space point velocity B - A, including rotation.
    pre_contact_time_s identifies an observed separated sample, not proof that
    the whole preceding motion is collision-free.
    """

    component_a_id: str
    component_b_id: str
    time_interval_s: tuple[float, float]
    earliest_contact_time_s: float | None
    state_time_s: float
    signed_distance_m: float | None
    confirmed: bool
    certainty: Literal["certified", "bracketed", "indeterminate"]
    event_type: Literal["contact", "clearance_violation", "initial_overlap", "possible_contact"]
    position_a_m: tuple[float, float, float] | None = None
    position_b_m: tuple[float, float, float] | None = None
    contact_normal: tuple[float, float, float] | None = None
    normal_source: str = "unavailable"
    relative_velocity_m_s: tuple[float, float, float] | None = None
    relative_speed_m_s: float | None = None
    closing_speed_m_s: float | None = None
    contact_angle_rad: float | None = None
    pre_contact_time_s: float | None = None
    pre_contact_relative_velocity_m_s: tuple[float, float, float] | None = None
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v.strip() for v in (self.component_a_id, self.component_b_id)) or self.component_a_id == self.component_b_id:
            raise ValueError("event requires distinct non-empty component IDs")
        times = tuple(_finite(t, "time_interval_s") for t in self.time_interval_s)
        if len(times) != 2 or times[0] > times[1]:
            raise ValueError("invalid event time interval")
        object.__setattr__(self, "time_interval_s", times)
        if not times[0] <= _finite(self.state_time_s, "state_time_s") <= times[1]:
            raise ValueError("event state time must lie in the reported interval")
        if not isinstance(self.confirmed, bool):
            raise TypeError("confirmed must be boolean")
        if self.certainty not in {"certified", "bracketed", "indeterminate"} or self.event_type not in {"contact", "clearance_violation", "initial_overlap", "possible_contact"}:
            raise ValueError("invalid event classification")
        if self.confirmed:
            if self.earliest_contact_time_s != self.state_time_s or self.event_type == "possible_contact":
                raise ValueError("confirmed event must identify the observed violation time")
        elif self.earliest_contact_time_s is not None or self.certainty != "indeterminate" or self.event_type != "possible_contact":
            raise ValueError("unconfirmed event cannot assert an impact time or contact")
        for name in ("position_a_m", "position_b_m", "contact_normal", "relative_velocity_m_s", "pre_contact_relative_velocity_m_s"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, _vector(getattr(self, name)))
        if self.contact_normal is not None and not math.isclose(math.hypot(*self.contact_normal), 1, abs_tol=1e-8):
            raise ValueError("contact normal must be a unit vector")
        for name in ("signed_distance_m", "closing_speed_m_s"):
            if getattr(self, name) is not None and not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite or None")
        if self.relative_speed_m_s is not None:
            _finite(self.relative_speed_m_s, "relative_speed_m_s")
        if self.contact_angle_rad is not None and not 0 <= self.contact_angle_rad <= math.pi:
            raise ValueError("contact angle must lie in [0, pi]")
        if self.pre_contact_time_s is not None and not 0 <= self.pre_contact_time_s < self.state_time_s:
            raise ValueError("pre-contact time must precede the event state")
        object.__setattr__(self, "evidence", tuple(self.evidence))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ContinuousContactEvent:
        data = dict(value)
        data["evidence"] = tuple(Evidence(**e) for e in data.get("evidence", ()))
        return cls(**data)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContinuousInterferenceReport(AgentReadableResult):
    """A conditional continuous verdict with certified and unresolved evidence.

    minimum_clearance_m is the minimum observed mesh-query distance, or None
    if bounding spheres suffice without mesh queries. clearance_lower_bound_m
    is a whole-scope bound and is None unless every interval is certified safe.
    Local safe bounds remain in metadata.certified_intervals. A confirmed
    collision keeps status failed even when later coverage or TOI refinement
    exhausts its budget; options, events and query counts are retained.
    """

    status: Literal["passed", "failed", "indeterminate", "capability_failed", "validation_failed", "partial"]
    options: ContinuousInterferenceOptions | None = None
    events: tuple[ContinuousContactEvent, ...] = ()
    checked_component_pair_count: int = 0
    query_count: int = 0
    subdivision_count: int = 0
    minimum_clearance_m: float | None = None
    clearance_lower_bound_m: float | None = None
    issues: tuple[SimIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in {"passed", "failed", "indeterminate", "capability_failed", "validation_failed", "partial"}:
            raise ValueError("invalid continuous check status")
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda e: (e.time_interval_s, e.component_a_id, e.component_b_id))))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        for name in ("checked_component_pair_count", "query_count", "subdivision_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("minimum_clearance_m", "clearance_lower_bound_m"):
            if getattr(self, name) is not None and not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite or None")
        if self.status == "passed" and (not self.checked_component_pair_count or self.events or any(i.severity == "error" for i in self.issues) or self.clearance_lower_bound_m is None or self.options is None or self.clearance_lower_bound_m <= self.options.minimum_clearance_m or not self.metadata.get("coverage_complete")):
            raise ValueError("a passed continuous report requires complete nonempty certified evidence")

    @property
    def operation(self) -> str:
        return "check_continuous_interference"

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    @property
    def first_failure_time_s(self) -> float | None:
        return min((e.state_time_s for e in self.events if e.confirmed), default=None)

    @property
    def report(self) -> DiagnosticReport:
        return DiagnosticReport(operation=self.operation, status=self.status, issues=self.issues, metadata=self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(), "schema_version": "kincheck.continuous/1.0",
            "operation": self.operation, "status": self.status, "passed": self.passed,
            "options": self.options.to_dict() if self.options else None,
            "events": [e.to_dict() for e in self.events],
            "checked_component_pair_count": self.checked_component_pair_count,
            "query_count": self.query_count, "subdivision_count": self.subdivision_count,
            "minimum_clearance_m": self.minimum_clearance_m,
            "clearance_lower_bound_m": self.clearance_lower_bound_m,
            "first_failure_time_s": self.first_failure_time_s,
            "issues": [i.to_dict() for i in self.issues], "metadata": _json_value(self.metadata),
        }

    def as_check_report(self, *, check_id: str = "continuous_interference"):
        from .checks import CheckReport
        return CheckReport(check_id=check_id, check_type="continuous_interference", passed=self.passed,
                           severity="info" if self.passed else "error", issues=self.issues,
                           evidence=(Evidence(key="query_count", actual=self.query_count), Evidence(key="clearance_lower_bound_m", actual=self.clearance_lower_bound_m, unit="m")), metadata=self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ContinuousInterferenceReport:
        if value.get("schema_version") != "kincheck.continuous/1.0":
            raise ValueError("unsupported continuous report schema")
        data = {name: value[name] for name in cls.__dataclass_fields__}
        data["options"] = ContinuousInterferenceOptions(**data["options"]) if data["options"] is not None else None
        data["events"] = tuple(ContinuousContactEvent.from_dict(e) for e in data["events"])
        data["issues"] = tuple(SimIssue(**{**i, "evidence": tuple(Evidence(**e) for e in i.get("evidence", ()))}) for i in data["issues"])
        return cls(**data)


__all__ = ["ContinuousInterferenceOptions", "ContinuousContactEvent", "ContinuousInterferenceReport"]
