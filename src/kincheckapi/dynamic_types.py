"""Public contracts for the v0.6.1-v0.6.3 dynamic checks.

The contracts intentionally describe scalar revolute/prismatic tree dynamics.
They carry SI values and JSON-safe evidence, while keeping MuJoCo objects
private to the solver implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Literal, Mapping

from .physics_types import GravityField, PhysicsReport, WrenchLoad, fail, plain
from .diagnostics import Evidence, SimIssue


def _issues(value):
    return tuple(
        SimIssue(**{**item, "evidence": tuple(Evidence(**e) for e in item.get("evidence", ()))})
        for item in value.get("issues", ())
    )


def _report_fields(value):
    return {
        "operation": value.get("operation", "dynamic"),
        "status": value.get("status", "failed"),
        "issues": _issues(value),
        "evidence": value.get("evidence", {}),
        "model_sha256": value.get("model_sha256"),
        "result_index": value.get("result_index"),
    }


def _id(value: str, name: str, operation: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail("VALUE-INVALID", f"{name} must be a non-empty string.", operation=operation)
    return value


def _finite(value: float, name: str, operation: str) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = math.nan
    if not math.isfinite(value):
        fail("VALUE-INVALID", f"{name} must be finite.", operation=operation)
    return value


def _vector(value, name: str, operation: str) -> tuple[float, float, float]:
    try:
        values = tuple(_finite(v, name, operation) for v in value)
    except TypeError:
        values = ()
    if len(values) != 3:
        fail("VALUE-INVALID", f"{name} must be a finite 3-vector.", operation=operation)
    return values  # type: ignore[return-value]


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicState:
    """One prescribed scalar joint state at an instant.

    Revolute values use rad/rad/s/rad/s2 and prismatic values use
    m/m/s/m/s2 according to the referenced Joint type.
    """

    joint_id: str
    position: float
    velocity: float = 0.0
    acceleration: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "joint_id", _id(self.joint_id, "joint_id", "DynamicState"))
        for name in ("position", "velocity", "acceleration"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, "DynamicState"))

    def to_dict(self):
        return plain(self)

    @property
    def position_rad_or_m(self):
        return self.position

    @property
    def velocity_rad_s_or_m_s(self):
        return self.velocity

    @property
    def acceleration_rad_s2_or_m_s2(self):
        return self.acceleration

    @classmethod
    def from_dict(cls, value):
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicRequest:
    """Inputs for one inverse-dynamics evaluation."""

    states: tuple[DynamicState, ...]
    gravity: GravityField = field(default_factory=lambda: GravityField(acceleration_m_s2=(0.0, 0.0, -9.81)))
    loads: tuple[WrenchLoad, ...] = ()

    def __post_init__(self):
        states = tuple(self.states)
        if not states:
            fail("STATE-INVALID", "At least one dynamic joint state is required.", operation="DynamicRequest")
        if any(not isinstance(s, DynamicState) for s in states):
            fail("STATE-INVALID", "Dynamic states must be typed and have unique joint IDs.", operation="DynamicRequest")
        ids = [s.joint_id for s in states]
        if len(set(ids)) != len(ids):
            fail("STATE-INVALID", "Dynamic states must be typed and have unique joint IDs.", operation="DynamicRequest")
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "loads", tuple(self.loads))

    @property
    def state_by_joint(self) -> Mapping[str, DynamicState]:
        return MappingProxyType({s.joint_id: s for s in self.states})

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(
            states=tuple(DynamicState.from_dict(item) for item in value["states"]),
            gravity=GravityField(**value["gravity"]),
            loads=tuple(WrenchLoad(**item) for item in value.get("loads", ())),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class InverseDynamicsResult(PhysicsReport):
    """Required generalized efforts and power at a prescribed state."""

    operation: str = "solve_inverse_dynamics"
    model_sha256: str | None = None
    request: DynamicRequest | None = None
    generalized_efforts: Mapping[str, float] = field(default_factory=dict)
    generalized_units: Mapping[str, str] = field(default_factory=dict)
    joint_powers_w: Mapping[str, float] = field(default_factory=dict)
    body_wrenches: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "generalized_efforts", MappingProxyType(dict(self.generalized_efforts)))
        object.__setattr__(self, "generalized_units", MappingProxyType(dict(self.generalized_units)))
        object.__setattr__(self, "joint_powers_w", MappingProxyType(dict(self.joint_powers_w)))
        object.__setattr__(self, "body_wrenches", MappingProxyType({k: MappingProxyType(dict(v)) for k, v in self.body_wrenches.items()}))
        if self.status in ("completed", "completed_with_warnings") and not self.generalized_efforts:
            fail(
                "RESULT-INCOMPLETE",
                "Completed inverse dynamics requires nonempty generalized efforts.",
                operation="InverseDynamicsResult",
            )
        if set(self.generalized_efforts) != set(self.generalized_units):
            fail("RESULT-INVALID", "Dynamic efforts and units must cover the same joints.", operation="InverseDynamicsResult")
        if set(self.joint_powers_w) - set(self.generalized_efforts):
            fail("RESULT-INVALID", "Dynamic power records reference unknown joints.", operation="InverseDynamicsResult")

    @classmethod
    def from_dict(cls, value):
        return cls(
            **_report_fields(value),
            request=None if value.get("request") is None else DynamicRequest.from_dict(value["request"]),
            generalized_efforts=value.get("generalized_efforts", {}),
            generalized_units=value.get("generalized_units", {}),
            joint_powers_w=value.get("joint_powers_w", {}),
            body_wrenches=value.get("body_wrenches", {}),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ActuatorSpec:
    """A finite ideal torque/force actuator bound to one scalar Joint."""

    actuator_id: str
    joint_id: str
    max_effort: float
    max_speed: float | None = None
    efficiency: float = 1.0

    def __post_init__(self):
        object.__setattr__(self, "actuator_id", _id(self.actuator_id, "actuator_id", "ActuatorSpec"))
        object.__setattr__(self, "joint_id", _id(self.joint_id, "joint_id", "ActuatorSpec"))
        effort = _finite(self.max_effort, "max_effort", "ActuatorSpec")
        if effort <= 0:
            fail("VALUE-INVALID", "max_effort must be positive.", operation="ActuatorSpec", objects=(self.actuator_id,))
        object.__setattr__(self, "max_effort", effort)
        if self.max_speed is not None:
            speed = _finite(self.max_speed, "max_speed", "ActuatorSpec")
            if speed <= 0:
                fail("VALUE-INVALID", "max_speed must be positive.", operation="ActuatorSpec", objects=(self.actuator_id,))
            object.__setattr__(self, "max_speed", speed)
        efficiency = _finite(self.efficiency, "efficiency", "ActuatorSpec")
        if not 0 < efficiency <= 1:
            fail("VALUE-INVALID", "efficiency must be in (0, 1].", operation="ActuatorSpec", objects=(self.actuator_id,))
        object.__setattr__(self, "efficiency", efficiency)

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ActuatorProfile:
    """A time-ordered public effort command, linearly interpolated."""

    actuator_id: str
    points: tuple[tuple[float, float], ...]

    def __post_init__(self):
        object.__setattr__(self, "actuator_id", _id(self.actuator_id, "actuator_id", "ActuatorProfile"))
        try:
            points = tuple((
                _finite(p[0], "time_s", "ActuatorProfile"),
                _finite(p[1], "effort", "ActuatorProfile"),
            ) for p in self.points)
        except (IndexError, KeyError, TypeError):
            fail("PROFILE-INVALID", "Each actuator profile point must contain time_s and effort.", operation="ActuatorProfile", objects=(self.actuator_id,))
        if not points or points[0][0] < 0 or any(b[0] <= a[0] for a, b in zip(points, points[1:])):
            fail("PROFILE-INVALID", "Actuator profile times must be nonempty and strictly increasing.", operation="ActuatorProfile", objects=(self.actuator_id,))
        object.__setattr__(self, "points", points)

    def value_at(self, time_s: float) -> float:
        time_s = _finite(time_s, "time_s", "ActuatorProfile.value_at")
        if time_s <= self.points[0][0]:
            return self.points[0][1]
        if time_s >= self.points[-1][0]:
            return self.points[-1][1]
        for (t0, v0), (t1, v1) in zip(self.points, self.points[1:]):
            if t0 <= time_s <= t1:
                fraction = (time_s - t0) / (t1 - t0)
                return v0 + fraction * (v1 - v0)
        return self.points[-1][1]

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(actuator_id=value["actuator_id"], points=tuple(tuple(item) for item in value["points"]))


@dataclass(frozen=True, slots=True, kw_only=True)
class ForwardDynamicsRequest:
    """Inputs for finite-actuator forward integration."""

    initial_states: tuple[DynamicState, ...]
    actuators: tuple[ActuatorSpec, ...]
    profiles: tuple[ActuatorProfile, ...]
    duration_s: float
    sample_period_s: float
    gravity: GravityField = field(default_factory=lambda: GravityField(acceleration_m_s2=(0.0, 0.0, -9.81)))
    loads: tuple[WrenchLoad, ...] = ()

    def __post_init__(self):
        states = tuple(self.initial_states)
        actuators = tuple(self.actuators)
        profiles = tuple(self.profiles)
        if not states or not actuators:
            fail("STATE-INVALID", "Forward dynamics requires initial states and actuators.", operation="ForwardDynamicsRequest")
        if any(not isinstance(s, DynamicState) for s in states) or any(not isinstance(a, ActuatorSpec) for a in actuators) or any(not isinstance(p, ActuatorProfile) for p in profiles):
            fail("STATE-INVALID", "Initial states, actuators, and profiles must use their typed contracts.", operation="ForwardDynamicsRequest")
        if len({s.joint_id for s in states}) != len(states) or len({a.actuator_id for a in actuators}) != len(actuators):
            fail("STATE-INVALID", "Initial states and actuators must have unique IDs.", operation="ForwardDynamicsRequest")
        actuator_ids = {a.actuator_id for a in actuators}
        if {p.actuator_id for p in profiles} != actuator_ids:
            fail("PROFILE-INVALID", "Exactly one effort profile is required for every actuator.", operation="ForwardDynamicsRequest")
        duration = _finite(self.duration_s, "duration_s", "ForwardDynamicsRequest")
        period = _finite(self.sample_period_s, "sample_period_s", "ForwardDynamicsRequest")
        if duration <= 0 or period <= 0:
            fail("TIME-INVALID", "duration_s and sample_period_s must be positive.", operation="ForwardDynamicsRequest")
        object.__setattr__(self, "initial_states", states)
        object.__setattr__(self, "actuators", actuators)
        object.__setattr__(self, "profiles", profiles)
        object.__setattr__(self, "duration_s", duration)
        object.__setattr__(self, "sample_period_s", period)
        object.__setattr__(self, "loads", tuple(self.loads))

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(
            initial_states=tuple(DynamicState.from_dict(item) for item in value["initial_states"]),
            actuators=tuple(ActuatorSpec.from_dict(item) for item in value["actuators"]),
            profiles=tuple(ActuatorProfile.from_dict(item) for item in value["profiles"]),
            duration_s=value["duration_s"],
            sample_period_s=value["sample_period_s"],
            gravity=GravityField(**value["gravity"]),
            loads=tuple(WrenchLoad(**item) for item in value.get("loads", ())),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicSample:
    time_s: float
    joint_positions: Mapping[str, float]
    joint_velocities: Mapping[str, float]
    joint_accelerations: Mapping[str, float]
    actuator_efforts: Mapping[str, float]

    def __post_init__(self):
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", "DynamicSample"))
        if self.time_s < 0:
            fail("RESULT-INVALID", "Dynamic sample time cannot be negative.", operation="DynamicSample")
        for name in ("joint_positions", "joint_velocities", "joint_accelerations", "actuator_efforts"):
            value = {str(k): _finite(v, name, "DynamicSample") for k, v in getattr(self, name).items()}
            object.__setattr__(self, name, MappingProxyType(value))

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ForwardDynamicsResult(PhysicsReport):
    operation: str = "solve_forward_dynamics"
    model_sha256: str | None = None
    request: ForwardDynamicsRequest | None = None
    samples: tuple[DynamicSample, ...] = ()
    energy_input_j: float = 0.0
    peak_power_w: float = 0.0
    peak_effort: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self):
        PhysicsReport.__post_init__(self)
        samples = tuple(self.samples)
        if self.status in ("completed", "completed_with_warnings") and not samples:
            fail(
                "RESULT-INCOMPLETE",
                "Completed forward dynamics requires nonempty dynamic samples.",
                operation="ForwardDynamicsResult",
            )
        if any(b.time_s <= a.time_s for a, b in zip(samples, samples[1:])):
            fail("RESULT-INVALID", "Dynamic samples must be strictly time ordered.", operation="ForwardDynamicsResult")
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "energy_input_j", _finite(self.energy_input_j, "energy_input_j", "ForwardDynamicsResult"))
        object.__setattr__(self, "peak_power_w", _finite(self.peak_power_w, "peak_power_w", "ForwardDynamicsResult"))
        object.__setattr__(self, "peak_effort", MappingProxyType(dict(self.peak_effort)))

    @classmethod
    def from_dict(cls, value):
        return cls(
            **_report_fields(value),
            request=None if value.get("request") is None else ForwardDynamicsRequest.from_dict(value["request"]),
            samples=tuple(DynamicSample.from_dict(item) for item in value.get("samples", ())),
            energy_input_j=value.get("energy_input_j", 0.0),
            peak_power_w=value.get("peak_power_w", 0.0),
            peak_effort=value.get("peak_effort", {}),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactSpec:
    """A declared planar contact capacity; normal points in the load direction."""

    contact_id: str
    normal: tuple[float, float, float]
    friction_coefficient: float
    contact_area_m2: float | None = None
    allowable_normal_force_n: float | None = None
    allowable_pressure_pa: float | None = None

    def __post_init__(self):
        object.__setattr__(self, "contact_id", _id(self.contact_id, "contact_id", "ContactSpec"))
        normal = _vector(self.normal, "normal", "ContactSpec")
        norm = math.sqrt(sum(v * v for v in normal))
        if abs(norm - 1.0) > 1e-9:
            fail("CONTACT-INVALID", "Contact normal must be unit length.", operation="ContactSpec", objects=(self.contact_id,))
        object.__setattr__(self, "normal", normal)
        mu = _finite(self.friction_coefficient, "friction_coefficient", "ContactSpec")
        if mu < 0:
            fail("CONTACT-INVALID", "friction_coefficient must be nonnegative.", operation="ContactSpec", objects=(self.contact_id,))
        object.__setattr__(self, "friction_coefficient", mu)
        for name in ("contact_area_m2", "allowable_normal_force_n", "allowable_pressure_pa"):
            value = getattr(self, name)
            if value is not None:
                value = _finite(value, name, "ContactSpec")
                if value <= 0:
                    fail("CONTACT-INVALID", f"{name} must be positive.", operation="ContactSpec", objects=(self.contact_id,))
                object.__setattr__(self, name, value)
        if self.allowable_pressure_pa is not None and self.contact_area_m2 is None:
            fail("CONTACT-INVALID", "contact_area_m2 is required with allowable_pressure_pa.", operation="ContactSpec", objects=(self.contact_id,))

    def to_dict(self):
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactReport(PhysicsReport):
    operation: str = "check_contact_capacity"
    contact_id: str = ""
    normal_force_n: float = 0.0
    tangential_force_n: float = 0.0
    friction_limit_n: float = 0.0
    pressure_pa: float | None = None
    utilization: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self):
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "contact_id", _id(self.contact_id, "contact_id", "ContactReport"))
        for name in ("normal_force_n", "tangential_force_n", "friction_limit_n"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, "ContactReport"))
        if self.pressure_pa is not None:
            object.__setattr__(self, "pressure_pa", _finite(self.pressure_pa, "pressure_pa", "ContactReport"))
        object.__setattr__(self, "utilization", MappingProxyType(dict(self.utilization)))

    @classmethod
    def from_dict(cls, value):
        return cls(**_report_fields(value), contact_id=value["contact_id"], normal_force_n=value.get("normal_force_n", 0.0), tangential_force_n=value.get("tangential_force_n", 0.0), friction_limit_n=value.get("friction_limit_n", 0.0), pressure_pa=value.get("pressure_pa"), utilization=value.get("utilization", {}))


__all__ = [
    "DynamicState", "DynamicRequest", "InverseDynamicsResult",
    "ActuatorSpec", "ActuatorProfile", "ForwardDynamicsRequest",
    "DynamicSample", "ForwardDynamicsResult", "ContactSpec", "ContactReport",
]
