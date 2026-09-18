"""Immutable public result models for geometric safety checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

from .diagnostics import AgentReadableResult, Evidence, SimIssue
from .result import InterferenceEvent


SamplingScope = Literal["motion_result", "solver_steps"]


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if hasattr(value, "to_dict"):
        return _json_value(value.to_dict())
    return repr(value)


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _vector(value: Sequence[float], name: str) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"{name} must contain three values")
    return tuple(_finite(item, name) for item in value)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvelopeSample:
    """World-space bounds of one real mesh at one recorded time."""

    time_s: float
    world_min_position_m: tuple[float, float, float]
    world_max_position_m: tuple[float, float, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        object.__setattr__(self, "world_min_position_m", _vector(self.world_min_position_m, "world_min_position_m"))
        object.__setattr__(self, "world_max_position_m", _vector(self.world_max_position_m, "world_max_position_m"))
        if any(low > high for low, high in zip(self.world_min_position_m, self.world_max_position_m)):
            raise ValueError("world_min_position_m cannot exceed world_max_position_m")

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class MinimumClearance:
    component_a_id: str
    component_b_id: str
    minimum_clearance_m: float
    time_s: float
    closest_point_a_m: tuple[float, float, float] | None = None
    closest_point_b_m: tuple[float, float, float] | None = None
    backend_id: str = "python-fcl"
    sampling_scope: SamplingScope = "motion_result"

    def __post_init__(self) -> None:
        if not self.component_a_id or not self.component_b_id:
            raise ValueError("Minimum-clearance component IDs must be non-empty")
        if self.component_a_id == self.component_b_id:
            raise ValueError("Minimum-clearance components must be distinct")
        object.__setattr__(self, "minimum_clearance_m", _finite(self.minimum_clearance_m, "minimum_clearance_m"))
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        if self.closest_point_a_m is not None:
            object.__setattr__(self, "closest_point_a_m", _vector(self.closest_point_a_m, "closest_point_a_m"))
        if self.closest_point_b_m is not None:
            object.__setattr__(self, "closest_point_b_m", _vector(self.closest_point_b_m, "closest_point_b_m"))
        if self.sampling_scope not in {"motion_result", "solver_steps"}:
            raise ValueError("sampling_scope must be motion_result or solver_steps")

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionEnvelope:
    component_id: str
    world_min_position_m: tuple[float, float, float]
    world_max_position_m: tuple[float, float, float]
    sample_times_s: tuple[float, ...]
    mesh_vertex_count: int
    mesh_path: str
    mesh_sha256: str | None = None
    mesh_triangle_count: int | None = None
    sample_bounds: tuple[EnvelopeSample, ...] = ()
    backend_id: str = "python-fcl"
    sampling_scope: SamplingScope = "motion_result"

    def __post_init__(self) -> None:
        object.__setattr__(self, "world_min_position_m", _vector(self.world_min_position_m, "world_min_position_m"))
        object.__setattr__(self, "world_max_position_m", _vector(self.world_max_position_m, "world_max_position_m"))
        if any(low > high for low, high in zip(self.world_min_position_m, self.world_max_position_m)):
            raise ValueError("world_min_position_m cannot exceed world_max_position_m")
        times = tuple(_finite(item, "sample_times_s") for item in self.sample_times_s)
        if not times or any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("sample_times_s must be strictly increasing")
        object.__setattr__(self, "sample_times_s", times)
        bounds = tuple(self.sample_bounds)
        if len(bounds) != len(times) or tuple(item.time_s for item in bounds) != times:
            raise ValueError("sample_bounds must contain one bound for every sample time")
        object.__setattr__(self, "sample_bounds", bounds)
        if self.mesh_vertex_count <= 0:
            raise ValueError("mesh_vertex_count must be positive")
        if self.mesh_triangle_count is not None and self.mesh_triangle_count <= 0:
            raise ValueError("mesh_triangle_count must be positive when provided")
        if self.sampling_scope not in {"motion_result", "solver_steps"}:
            raise ValueError("sampling_scope must be motion_result or solver_steps")

    @property
    def sampling_period_s(self) -> float:
        return max((right - left for left, right in zip(self.sample_times_s, self.sample_times_s[1:])), default=0.0)

    def to_dict(self) -> dict[str, Any]:
        return {**_json_value(asdict(self)), "sampling_period_s": self.sampling_period_s}


@dataclass(frozen=True, slots=True, kw_only=True)
class ClearanceReport(AgentReadableResult):
    operation: Literal["interference", "minimum_clearance", "motion_envelope"]
    passed: bool
    status: Literal["passed", "failed", "capability_failed", "partial"]
    events: tuple[InterferenceEvent, ...] = ()
    measurements: tuple[MinimumClearance, ...] = ()
    envelopes: tuple[MotionEnvelope, ...] = ()
    checked_component_pair_count: int = 0
    checked_sample_count: int = 0
    first_failure_time_s: float | None = None
    maximum_penetration_depth_m: float = 0.0
    backend_id: str | None = "python-fcl"
    backend_version: str | None = None
    sampling_scope: SamplingScope = "motion_result"
    sampling_period_s: float = 0.0
    issues: tuple[SimIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in {"passed", "failed", "capability_failed", "partial"}:
            raise ValueError("Invalid clearance status")
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda item: (item.time_s, item.component_a_id, item.component_b_id))))
        object.__setattr__(self, "measurements", tuple(sorted(self.measurements, key=lambda item: (item.time_s, item.component_a_id, item.component_b_id))))
        object.__setattr__(self, "envelopes", tuple(sorted(self.envelopes, key=lambda item: item.component_id)))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "maximum_penetration_depth_m", max(0.0, _finite(self.maximum_penetration_depth_m, "maximum_penetration_depth_m")))
        object.__setattr__(self, "sampling_period_s", max(0.0, _finite(self.sampling_period_s, "sampling_period_s")))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "operation": self.operation, "passed": self.passed, "status": self.status,
            "events": [item.to_dict() for item in self.events], "measurements": [item.to_dict() for item in self.measurements],
            "envelopes": [item.to_dict() for item in self.envelopes], "checked_component_pair_count": self.checked_component_pair_count,
            "checked_sample_count": self.checked_sample_count, "first_failure_time_s": self.first_failure_time_s,
            "maximum_penetration_depth_m": self.maximum_penetration_depth_m, "backend_id": self.backend_id,
            "backend_version": self.backend_version, "sampling_scope": self.sampling_scope, "sampling_period_s": self.sampling_period_s,
            "issues": [item.to_dict() for item in self.issues], "metadata": _json_value(self.metadata),
        }

    def as_check_report(self, *, check_id: str | None = None):
        from .checks import CheckReport

        evidence = (
            Evidence(key="checked_component_pair_count", actual=self.checked_component_pair_count),
            Evidence(key="checked_sample_count", actual=self.checked_sample_count),
            Evidence(key="sampling_scope", actual=self.sampling_scope),
            Evidence(key="sampling_period_s", actual=self.sampling_period_s, unit="s"),
            Evidence(key="maximum_penetration_depth_m", actual=self.maximum_penetration_depth_m, unit="m"),
        )
        if self.operation == "minimum_clearance":
            evidence += (Evidence(key="minimum_clearance_m", actual=min((item.minimum_clearance_m for item in self.measurements), default=None), unit="m"),)
        return CheckReport(check_id=check_id or self.operation, check_type=self.operation, passed=self.passed, severity="error" if not self.passed else "info", evidence=evidence, issues=self.issues, metadata=self.to_dict())


__all__ = ["ClearanceReport", "EnvelopeSample", "MinimumClearance", "MotionEnvelope", "SamplingScope"]
