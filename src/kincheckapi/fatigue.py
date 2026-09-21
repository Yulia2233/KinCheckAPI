"""High-cycle fatigue and operating-envelope reference calculations (0.6.6)."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .physics_types import PhysicsReport, fail, plain
from .structural import _finite, _issue, _positive


@dataclass(frozen=True, slots=True, kw_only=True)
class StressHistory:
    history_id: str
    times_s: tuple[float, ...]
    stress_pa: tuple[float, ...]
    unit: str = "Pa"
    region_id: str = ""
    case_id: str = ""
    coordinate_frame: str = "material"

    def __post_init__(self) -> None:
        if not self.history_id or not self.unit:
            fail("HISTORY-INVALID", "Stress history requires an ID and unit.", operation="StressHistory")
        times = tuple(_finite(v, "time_s", "StressHistory") for v in self.times_s)
        stress = tuple(_finite(v, "stress_pa", "StressHistory") for v in self.stress_pa)
        if len(times) != len(stress) or len(times) < 2 or any(b <= a for a, b in zip(times, times[1:])):
            fail("HISTORY-INVALID", "Stress history times must be strictly increasing and match stress samples.", operation="StressHistory")
        object.__setattr__(self, "times_s", times); object.__setattr__(self, "stress_pa", stress)

    @property
    def duration_s(self) -> float:
        return self.times_s[-1] - self.times_s[0]


@dataclass(frozen=True, slots=True, kw_only=True)
class FatigueMaterial:
    material_id: str
    sn_points: tuple[tuple[float, float], ...]
    ultimate_strength_pa: float | None = None
    fatigue_limit_pa: float | None = None
    source: str = "declared"
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if not self.material_id or not self.source:
            fail("MATERIAL-MISSING", "Fatigue material requires identity and source.", operation="FatigueMaterial")
        points = tuple((_positive(s, "sn_stress_pa", "FatigueMaterial"), _positive(n, "sn_cycles", "FatigueMaterial")) for s, n in self.sn_points)
        if len(points) < 2 or any(b[0] >= a[0] or b[1] <= a[1] for a, b in zip(points, points[1:])):
            fail("SN-CURVE-INVALID", "S-N points must decrease in stress and increase in cycles.", operation="FatigueMaterial")
        object.__setattr__(self, "sn_points", points)
        for name in ("ultimate_strength_pa", "fatigue_limit_pa"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _positive(value, name, "FatigueMaterial"))
        conf = _finite(self.confidence, "confidence", "FatigueMaterial")
        if not 0 <= conf <= 1:
            fail("VALUE-INVALID", "confidence must lie in [0, 1].", operation="FatigueMaterial")
        object.__setattr__(self, "confidence", conf)

    def cycles_at(self, alternating_stress_pa: float) -> float:
        stress = abs(float(alternating_stress_pa))
        if stress <= 0:
            return math.inf
        points = self.sn_points
        if stress < points[-1][0]:
            return math.inf if self.fatigue_limit_pa is not None and stress <= self.fatigue_limit_pa else math.nan
        if stress > points[0][0]:
            return math.nan
        elif stress <= points[-1][0]:
            i, j = len(points) - 2, len(points) - 1
        else:
            i = next(k for k, (a, b) in enumerate(zip(points, points[1:])) if a[0] >= stress >= b[0]); j = i + 1
        s0, n0 = points[i]; s1, n1 = points[j]
        slope = (math.log(n1) - math.log(n0)) / (math.log(s1) - math.log(s0))
        return math.exp(math.log(n0) + slope * (math.log(stress) - math.log(s0)))


@dataclass(frozen=True, slots=True, kw_only=True)
class MeanStressCorrection:
    method: str = "goodman"
    ultimate_strength_pa: float | None = None

    def __post_init__(self) -> None:
        if self.method not in ("none", "goodman", "gerber"):
            fail("MEAN-STRESS-UNSUPPORTED", f"Unsupported mean-stress correction {self.method!r}.", operation="MeanStressCorrection")
        if self.method != "none" and (self.ultimate_strength_pa is None or self.ultimate_strength_pa <= 0):
            fail("MEAN-STRESS-MISSING", "Goodman and Gerber corrections require ultimate_strength_pa.", operation="MeanStressCorrection")

    def corrected_amplitude(self, amplitude_pa: float, mean_pa: float) -> float:
        a = abs(float(amplitude_pa)); m = float(mean_pa)
        if self.method == "none":
            return a
        su = float(self.ultimate_strength_pa)
        if self.method == "goodman":
            denominator = 1.0 - m / su
            if denominator <= 0:
                return math.inf
            return a / denominator
        denominator = 1.0 - (m / su) ** 2
        if denominator <= 0:
            return math.inf
        return a / denominator


@dataclass(frozen=True, slots=True, kw_only=True)
class FatigueCycle:
    stress_range_pa: float
    mean_stress_pa: float
    count: float
    start_index: int | None = None
    end_index: int | None = None

    @property
    def amplitude_pa(self) -> float:
        return abs(self.stress_range_pa) / 2.0


@dataclass(frozen=True, slots=True, kw_only=True)
class FatigueReport(PhysicsReport):
    operation: str = "evaluate_fatigue"
    history_id: str = ""
    material_id: str = ""
    cycles: tuple[FatigueCycle, ...] = ()
    damage: float = 0.0
    allowable_damage: float = 1.0
    life_repeats: float = math.inf
    correction: str = "none"
    residual_indices: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "cycles", tuple(self.cycles))
        object.__setattr__(self, "damage", _finite(self.damage, "damage", self.operation))
        object.__setattr__(self, "allowable_damage", _positive(self.allowable_damage, "allowable_damage", self.operation))
        object.__setattr__(self, "life_repeats", _finite(self.life_repeats, "life_repeats", self.operation) if math.isfinite(self.life_repeats) else math.inf)

    def to_dict(self) -> dict[str, Any]:
        payload = PhysicsReport.to_dict(self)
        if math.isinf(self.life_repeats):
            payload["life_repeats"] = None
            payload["life_repeats_is_infinite"] = True
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FatigueReport":
        cycles = tuple(FatigueCycle(**item) for item in value.get("cycles", ()))
        life = math.inf if value.get("life_repeats_is_infinite") or value.get("life_repeats") is None else value.get("life_repeats")
        return cls(operation=value.get("operation", "evaluate_fatigue"), status=value.get("status", "failed"), evidence=value.get("evidence", {}), history_id=value.get("history_id", ""), material_id=value.get("material_id", ""), cycles=cycles, damage=value.get("damage", 0.0), allowable_damage=value.get("allowable_damage", 1.0), life_repeats=life, correction=value.get("correction", "none"), residual_indices=tuple(value.get("residual_indices", ())))


@dataclass(frozen=True, slots=True, kw_only=True)
class DutyCycle:
    duty_id: str
    stages: tuple[tuple[str, int], ...]
    source: str = "declared"

    def __post_init__(self) -> None:
        if not self.duty_id or not self.stages:
            fail("DUTY-INVALID", "Duty cycle requires an ID and at least one stage.", operation="DutyCycle")
        for case, count in self.stages:
            if not case or not isinstance(count, int) or count <= 0:
                fail("DUTY-INVALID", "Duty stages require positive integer repetition counts.", operation="DutyCycle")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScenarioMatrix:
    cases: Mapping[str, Mapping[str, Any]]
    search_strategy: str = "declared"

    def __post_init__(self) -> None:
        if not self.cases:
            fail("SCENARIO-MISSING", "Scenario matrix cannot be empty.", operation="ScenarioMatrix")
        if self.search_strategy not in ("declared", "grid", "sampled"):
            fail("SCENARIO-INVALID", "Unsupported scenario search strategy.", operation="ScenarioMatrix")


@dataclass(frozen=True, slots=True, kw_only=True)
class OperatingEnvelopeReport(PhysicsReport):
    operation: str = "evaluate_operating_envelope"
    case_reports: Mapping[str, FatigueReport] = field(default_factory=dict)
    worst_case_id: str | None = None
    worst_damage: float = 0.0
    evaluated_count: int = 0
    requested_count: int = 0

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "case_reports", dict(self.case_reports))
        object.__setattr__(self, "worst_damage", _finite(self.worst_damage, "worst_damage", self.operation))

    def to_dict(self) -> dict[str, Any]:
        payload = PhysicsReport.to_dict(self)
        payload["case_reports"] = {case_id: report.to_dict() for case_id, report in self.case_reports.items()}
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class DriveDutySummary(PhysicsReport):
    operation: str = "summarize_drive_duty"
    torque_peak_nm: float = 0.0
    torque_rms_nm: float = 0.0
    speed_peak_rad_s: float = 0.0
    power_peak_w: float = 0.0
    energy_positive_j: float = 0.0
    energy_negative_j: float = 0.0
    energy_net_j: float = 0.0


def _turning_points(values: Sequence[float]) -> list[tuple[int, float]]:
    points = [(i, float(v)) for i, v in enumerate(values)]
    if len(points) < 2:
        return points
    result = [points[0]]
    for index, item in enumerate(points[1:-1], start=1):
        if (item[1] - result[-1][1]) == 0:
            continue
        if (item[1] - result[-1][1]) * (points[index + 1][1] - item[1]) < 0:
            result.append(item)
    result.append(points[-1])
    return result


def count_cycles(*, stress_pa: Sequence[float], retain_residual: bool = True) -> tuple[FatigueCycle, ...]:
    """Count cycles with the ASTM four-point rainflow stack."""
    values = tuple(_finite(v, "stress_pa", "count_cycles") for v in stress_pa)
    if len(values) < 2:
        raise ValueError("stress_pa requires at least two samples")
    turning = _turning_points(values)
    stack: list[tuple[int, float]] = []
    cycles: list[FatigueCycle] = []
    for index, value in turning:
        stack.append((index, value))
        while len(stack) >= 3:
            x = abs(stack[-2][1] - stack[-3][1]); y = abs(stack[-1][1] - stack[-2][1])
            if y < x:
                break
            i0, s0 = stack[-3]; i1, s1 = stack[-2]; count = 1.0 if len(stack) > 3 else 0.5
            cycles.append(FatigueCycle(stress_range_pa=abs(s1 - s0), mean_stress_pa=(s1 + s0) / 2.0, count=count, start_index=i0, end_index=i1))
            del stack[-2]
    if retain_residual:
        for (i0, s0), (i1, s1) in zip(stack, stack[1:]):
            if s0 != s1:
                cycles.append(FatigueCycle(stress_range_pa=abs(s1 - s0), mean_stress_pa=(s1 + s0) / 2.0, count=0.5, start_index=i0, end_index=i1))
    return tuple(cycles)


def evaluate_fatigue(*, history: StressHistory, material: FatigueMaterial, correction: MeanStressCorrection = MeanStressCorrection(method="none"), repeat_count: int = 1, allowable_damage: float = 1.0) -> FatigueReport:
    op = "evaluate_fatigue"
    if not isinstance(repeat_count, int) or repeat_count <= 0:
        return FatigueReport(status="validation_failed", issues=(_issue("DUTY-INVALID", "repeat_count must be a positive integer.", op),), history_id=history.history_id, material_id=material.material_id)
    allowable = _positive(allowable_damage, "allowable_damage", op)
    cycles = count_cycles(stress_pa=history.stress_pa)
    damage = 0.0; extrapolated = 0; mean_unsupported = False; sn_unsupported = False
    for cycle in cycles:
        adjusted = correction.corrected_amplitude(cycle.amplitude_pa, cycle.mean_stress_pa)
        if not math.isfinite(adjusted):
            mean_unsupported = True; continue
        life = material.cycles_at(adjusted)
        if not math.isfinite(life) and life != math.inf:
            sn_unsupported = True; continue
        if adjusted > material.sn_points[0][0] or adjusted < material.sn_points[-1][0]:
            extrapolated += 1
        if math.isfinite(life):
            damage += cycle.count * repeat_count / life
    status = "failed" if damage > allowable else ("indeterminate" if mean_unsupported or sn_unsupported else "passed")
    issues = ()
    if mean_unsupported:
        issues += (_issue("MEAN-STRESS-OUT-OF-DOMAIN", "Mean-stress correction leaves the material domain.", op),)
    if sn_unsupported:
        issues += (_issue("SN-CURVE-OUT-OF-DOMAIN", "A corrected stress amplitude lies outside the declared S-N curve domain.", op),)
    if status == "failed":
        issues += (_issue("FATIGUE-DAMAGE-EXCEEDED", "Miner cumulative damage exceeds the declared allowable.", op, actual=damage, expected=allowable),)
    life_repeats = math.inf if damage == 0 else allowable / damage
    return FatigueReport(status=status, issues=issues, history_id=history.history_id, material_id=material.material_id, cycles=cycles, damage=damage, allowable_damage=allowable, life_repeats=life_repeats, correction=correction.method, residual_indices=tuple(c.end_index for c in cycles if c.count == 0.5), evidence={"repeat_count": repeat_count, "extrapolated_cycle_count": extrapolated, "stress_definition": "signed uniaxial stress; amplitude=range/2", "miner_rule": "linear"})


def evaluate_operating_envelope(*, cases: Mapping[str, tuple[StressHistory, FatigueMaterial]], correction: MeanStressCorrection = MeanStressCorrection(method="none"), allowable_damage: float = 1.0, scenario_matrix: ScenarioMatrix | None = None) -> OperatingEnvelopeReport:
    reports = {case_id: evaluate_fatigue(history=history, material=material, correction=correction, allowable_damage=allowable_damage) for case_id, (history, material) in cases.items()}
    worst_id, worst = (max(reports.items(), key=lambda item: item[1].damage) if reports else (None, None))
    requested_ids = set(scenario_matrix.cases) if scenario_matrix else set(cases)
    actual_ids = set(cases)
    missing = sorted(requested_ids - actual_ids)
    extra = sorted(actual_ids - requested_ids) if scenario_matrix else []
    requested = len(requested_ids)
    reports_failed = any(report.status == "failed" for report in reports.values())
    reports_unresolved = any(report.status in {"indeterminate", "capability_failed", "validation_failed"} for report in reports.values())
    status = "failed" if reports_failed else ("indeterminate" if missing or extra or reports_unresolved or len(reports) < requested else "passed")
    issues = tuple(item for report in reports.values() for item in report.issues)
    if missing:
        issues += (_issue("SCENARIO-COVERAGE-MISSING", "Scenario matrix cases were not evaluated.", "evaluate_operating_envelope", actual=sorted(actual_ids), expected=sorted(requested_ids)),)
    if extra:
        issues += (_issue("SCENARIO-UNREQUESTED", "Evaluation contains case IDs absent from the requested scenario matrix.", "evaluate_operating_envelope", actual=sorted(actual_ids), expected=sorted(requested_ids)),)
    return OperatingEnvelopeReport(status=status, issues=issues, case_reports=reports, worst_case_id=worst_id, worst_damage=worst.damage if worst else 0.0, evaluated_count=len(reports), requested_count=requested, evidence={"search_strategy": scenario_matrix.search_strategy if scenario_matrix else "declared", "coverage_fraction": len(reports) / requested if requested else 0.0, "missing_case_ids": missing, "extra_case_ids": extra})


def summarize_drive_duty(*, times_s: Sequence[float], torque_nm: Sequence[float], speed_rad_s: Sequence[float]) -> DriveDutySummary:
    op = "summarize_drive_duty"
    t = np.asarray(times_s, dtype=float); torque = np.asarray(torque_nm, dtype=float); speed = np.asarray(speed_rad_s, dtype=float)
    if t.ndim != 1 or len(t) < 2 or torque.shape != t.shape or speed.shape != t.shape or not np.isfinite(np.concatenate((t, torque, speed))).all() or np.any(np.diff(t) <= 0):
        return DriveDutySummary(status="validation_failed", issues=(_issue("TIME-INVALID", "Drive duty arrays must be finite, aligned and strictly time ordered.", op),))
    power = torque * speed
    duration = float(t[-1] - t[0]); square = torque * torque
    trapz = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    rms = math.sqrt(float(trapz(square, t) / duration)); positive_energy = float(trapz(np.maximum(power, 0), t)); negative_energy = float(trapz(np.minimum(power, 0), t));
    return DriveDutySummary(status="completed", torque_peak_nm=float(np.max(np.abs(torque))), torque_rms_nm=rms, speed_peak_rad_s=float(np.max(np.abs(speed))), power_peak_w=float(np.max(np.abs(power))), energy_positive_j=positive_energy, energy_negative_j=negative_energy, energy_net_j=positive_energy + negative_energy, evidence={"duration_s": duration, "integration": "trapezoid", "thermal_model": "not evaluated"})


def summarize_energy(*, times_s: Sequence[float], torque_nm: Sequence[float], speed_rad_s: Sequence[float]) -> PhysicsReport:
    summary = summarize_drive_duty(times_s=times_s, torque_nm=torque_nm, speed_rad_s=speed_rad_s)
    return PhysicsReport(operation="summarize_energy", status=summary.status, issues=summary.issues, evidence=summary.to_dict())


def check_fatigue_limits(*, result: FatigueReport, allowable_damage: float | None = None) -> PhysicsReport:
    bound = result.allowable_damage if allowable_damage is None else _positive(allowable_damage, "allowable_damage", "check_fatigue_limits")
    status = "passed" if result.damage <= bound and result.status == "passed" else ("failed" if result.damage > bound else "indeterminate")
    return PhysicsReport(operation="check_fatigue_limits", status=status, issues=() if status == "passed" else (_issue("FATIGUE-DAMAGE-EXCEEDED", "Fatigue damage is outside the declared limit or the input result is unresolved.", "check_fatigue_limits", actual=result.damage, expected=bound),), evidence={"damage": result.damage, "allowable_damage": bound, "life_repeats": result.life_repeats})


__all__ = ["StressHistory", "FatigueMaterial", "MeanStressCorrection", "FatigueCycle", "FatigueReport", "DutyCycle", "ScenarioMatrix", "OperatingEnvelopeReport", "DriveDutySummary", "count_cycles", "evaluate_fatigue", "evaluate_operating_envelope", "summarize_drive_duty", "summarize_energy", "check_fatigue_limits"]
