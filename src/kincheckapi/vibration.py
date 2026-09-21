"""Linear vibration, modal and random-response reference calculations (0.6.5)."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigh
from scipy.signal import welch

from .diagnostics import SimIssue
from .physics_types import PhysicsReport, fail, issue, plain
from .structural import StructuralModel, _finite, _issue, _matrix, _positive


@dataclass(frozen=True, slots=True, kw_only=True)
class ModalRequest:
    mode_count: int = 6
    fixed_dofs: tuple[int, ...] = ()
    frequency_min_hz: float = 0.0
    frequency_max_hz: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode_count, int) or self.mode_count < 1:
            fail("VALUE-INVALID", "mode_count must be a positive integer.", operation="ModalRequest")
        object.__setattr__(self, "fixed_dofs", tuple(int(i) for i in self.fixed_dofs))
        lo = _finite(self.frequency_min_hz, "frequency_min_hz", "ModalRequest")
        if lo < 0:
            fail("VALUE-INVALID", "frequency_min_hz cannot be negative.", operation="ModalRequest")
        object.__setattr__(self, "frequency_min_hz", lo)
        if self.frequency_max_hz is not None:
            hi = _finite(self.frequency_max_hz, "frequency_max_hz", "ModalRequest")
            if hi <= lo:
                fail("VALUE-INVALID", "frequency_max_hz must exceed frequency_min_hz.", operation="ModalRequest")
            object.__setattr__(self, "frequency_max_hz", hi)


@dataclass(frozen=True, slots=True, kw_only=True)
class DampingSpec:
    modal_ratios: tuple[float, ...] = ()
    rayleigh_alpha_s: float | None = None
    rayleigh_beta_s: float | None = None
    source: str = "declared"

    def __post_init__(self) -> None:
        ratios = tuple(_finite(v, "modal_ratio", "DampingSpec") for v in self.modal_ratios)
        if any(v < 0 for v in ratios):
            fail("DAMPING-INVALID", "Modal damping ratios cannot be negative.", operation="DampingSpec")
        object.__setattr__(self, "modal_ratios", ratios)
        for name in ("rayleigh_alpha_s", "rayleigh_beta_s"):
            value = getattr(self, name)
            if value is not None:
                value = _finite(value, name, "DampingSpec")
                if value < 0:
                    fail("DAMPING-INVALID", f"{name} cannot be negative.", operation="DampingSpec")
                object.__setattr__(self, name, value)
        if not self.source:
            fail("DAMPING-INVALID", "Damping source is required.", operation="DampingSpec")

    def ratio(self, frequency_hz: float, mode_index: int = 0) -> float:
        if self.modal_ratios:
            return self.modal_ratios[min(mode_index, len(self.modal_ratios) - 1)]
        omega = 2.0 * math.pi * max(frequency_hz, 0.0)
        c = (self.rayleigh_alpha_s or 0.0) / (2.0 * max(omega, 1e-30)) + (self.rayleigh_beta_s or 0.0) * omega / 2.0
        return max(0.0, c)


@dataclass(frozen=True, slots=True, kw_only=True)
class ModalResult(PhysicsReport):
    operation: str = "solve_modes"
    model_sha256: str | None = None
    frequencies_hz: tuple[float, ...] = ()
    mode_shapes: tuple[tuple[float, ...], ...] = ()
    effective_modal_mass: tuple[float, ...] = ()
    omitted_frequency_hz: float | None = None
    normalized: str = "mass"

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "frequencies_hz", tuple(_finite(v, "frequency_hz", self.operation) for v in self.frequencies_hz))
        object.__setattr__(self, "mode_shapes", tuple(tuple(_finite(v, "mode_shape", self.operation) for v in row) for row in self.mode_shapes))
        object.__setattr__(self, "effective_modal_mass", tuple(_finite(v, "effective_modal_mass", self.operation) for v in self.effective_modal_mass))
        if self.omitted_frequency_hz is not None:
            object.__setattr__(self, "omitted_frequency_hz", _finite(self.omitted_frequency_hz, "omitted_frequency_hz", self.operation))


@dataclass(frozen=True, slots=True, kw_only=True)
class FrequencyResponseResult(PhysicsReport):
    operation: str = "solve_frequency_response"
    model_sha256: str | None = None
    frequencies_hz: tuple[float, ...] = ()
    response: tuple[tuple[complex, ...], ...] = ()
    peak_amplitude: Mapping[str, float] = field(default_factory=dict)
    damping: DampingSpec | None = None

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "frequencies_hz", tuple(_finite(v, "frequency_hz", self.operation) for v in self.frequencies_hz))
        object.__setattr__(self, "response", tuple(tuple(complex(v) for v in row) for row in self.response))
        object.__setattr__(self, "peak_amplitude", {str(k): _finite(v, "peak_amplitude", self.operation) for k, v in self.peak_amplitude.items()})


@dataclass(frozen=True, slots=True, kw_only=True)
class TransientResult(PhysicsReport):
    operation: str = "solve_transient_response"
    model_sha256: str | None = None
    times_s: tuple[float, ...] = ()
    displacement_m: tuple[tuple[float, ...], ...] = ()
    velocity_m_s: tuple[tuple[float, ...], ...] = ()
    acceleration_m_s2: tuple[tuple[float, ...], ...] = ()
    time_step_s: float = 0.0

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "times_s", tuple(_finite(v, "time_s", self.operation) for v in self.times_s))
        for name in ("displacement_m", "velocity_m_s", "acceleration_m_s2"):
            object.__setattr__(self, name, tuple(tuple(_finite(v, name, self.operation) for v in row) for row in getattr(self, name)))
        object.__setattr__(self, "time_step_s", _finite(self.time_step_s, "time_step_s", self.operation))


@dataclass(frozen=True, slots=True, kw_only=True)
class RandomLoadSpec:
    frequency_hz: tuple[float, ...]
    psd: tuple[float, ...]
    unit: str
    seed: int | None = None
    one_sided: bool = True
    source: str = "declared"

    def __post_init__(self) -> None:
        f = tuple(_finite(v, "frequency_hz", "RandomLoadSpec") for v in self.frequency_hz)
        p = tuple(_finite(v, "psd", "RandomLoadSpec") for v in self.psd)
        if len(f) != len(p) or len(f) < 2 or any(b <= a for a, b in zip(f, f[1:])) or f[0] < 0 or any(v < 0 for v in p):
            fail("PSD-INVALID", "PSD frequencies must be increasing and PSD values nonnegative with matching lengths.", operation="RandomLoadSpec")
        if not self.unit:
            fail("PSD-INVALID", "PSD unit is required.", operation="RandomLoadSpec")
        object.__setattr__(self, "frequency_hz", f)
        object.__setattr__(self, "psd", p)


@dataclass(frozen=True, slots=True, kw_only=True)
class PSDResult(PhysicsReport):
    operation: str = "estimate_psd"
    frequency_hz: tuple[float, ...] = ()
    psd: tuple[float, ...] = ()
    unit: str = ""
    variance: float = 0.0
    sample_rate_hz: float = 0.0
    segment_count: int = 0

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "frequency_hz", tuple(_finite(v, "frequency_hz", self.operation) for v in self.frequency_hz))
        object.__setattr__(self, "psd", tuple(_finite(v, "psd", self.operation) for v in self.psd))
        object.__setattr__(self, "variance", _finite(self.variance, "variance", self.operation))
        object.__setattr__(self, "sample_rate_hz", _positive(self.sample_rate_hz, "sample_rate_hz", self.operation))


def _reduced(model: StructuralModel, fixed_dofs: Sequence[int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fixed = set(model.fixed_dofs) | {int(i) for i in fixed_dofs}
    free = np.array([i for i in range(model.dof_count) if i not in fixed], dtype=int)
    return np.asarray(model.stiffness_matrix, dtype=float)[np.ix_(free, free)], np.asarray(model.mass_matrix, dtype=float)[np.ix_(free, free)], free


def solve_modes(*, model: StructuralModel, request: ModalRequest = ModalRequest()) -> ModalResult:
    op = "solve_modes"
    if model.mass_matrix is None:
        return ModalResult(status="capability_failed", issues=(_issue("MASS-MISSING", "Modal analysis requires an explicit positive mass matrix.", op),), model_sha256=model.content_hash)
    try:
        K, M, free = _reduced(model, request.fixed_dofs)
        if len(free) == 0:
            return ModalResult(status="validation_failed", issues=(_issue("BOUNDARY-INVALID", "All structural DOFs are constrained.", op),), model_sha256=model.content_hash)
        values, vectors = eigh(K, M, subset_by_index=[0, min(request.mode_count, len(free)) - 1])
        if values[0] < -1e-8:
            return ModalResult(status="indeterminate", issues=(_issue("STIFFNESS-NOT-POSITIVE", "The constrained stiffness has a negative eigenvalue.", op, actual=float(values[0]), expected=">= 0"),), model_sha256=model.content_hash)
        values = np.maximum(values, 0.0)
        frequencies = np.sqrt(values) / (2 * math.pi)
        shapes = np.zeros((len(frequencies), model.dof_count))
        shapes[:, free] = vectors.T
        masses = tuple(float(v.T @ M @ v) for v in vectors.T)
        omitted = float(math.sqrt(max(values[-1], 0.0)) / (2 * math.pi)) if len(frequencies) < len(free) else None
        evidence = {"free_dofs": free.tolist(), "mass_normalized": True, "rigid_body_modes": int(np.count_nonzero(frequencies < 1e-8)), "frequency_band_hz": [request.frequency_min_hz, request.frequency_max_hz]}
        return ModalResult(status="completed", model_sha256=model.content_hash, frequencies_hz=tuple(float(v) for v in frequencies), mode_shapes=tuple(tuple(float(v) for v in row) for row in shapes), effective_modal_mass=masses, omitted_frequency_hz=omitted, evidence=evidence)
    except (np.linalg.LinAlgError, ValueError) as exc:
        return ModalResult(status="indeterminate", issues=(_issue("MODAL-SOLVE-FAILED", str(exc), op),), model_sha256=model.content_hash)


def solve_frequency_response(*, model: StructuralModel, frequencies_hz: Sequence[float], force_vector: Sequence[float], damping: DampingSpec = DampingSpec()) -> FrequencyResponseResult:
    op = "solve_frequency_response"
    if model.mass_matrix is None:
        return FrequencyResponseResult(status="capability_failed", issues=(_issue("MASS-MISSING", "Frequency response requires an explicit mass matrix.", op),), model_sha256=model.content_hash, damping=damping)
    frequencies = tuple(_finite(v, "frequency_hz", op) for v in frequencies_hz)
    if len(frequencies) == 0 or frequencies[0] < 0 or any(b < a for a, b in zip(frequencies, frequencies[1:])):
        return FrequencyResponseResult(status="validation_failed", issues=(_issue("FREQUENCY-INVALID", "frequencies_hz must be nonnegative and sorted.", op),), model_sha256=model.content_hash, damping=damping)
    force = np.asarray(force_vector, dtype=float)
    if force.shape != (model.dof_count,) or not np.isfinite(force).all():
        return FrequencyResponseResult(status="validation_failed", issues=(_issue("LOAD-INVALID", "force_vector must cover every structural DOF.", op),), model_sha256=model.content_hash, damping=damping)
    fixed = set(model.fixed_dofs)
    free = np.array([i for i in range(model.dof_count) if i not in fixed], dtype=int)
    K = np.asarray(model.stiffness_matrix)[np.ix_(free, free)]
    M = np.asarray(model.mass_matrix)[np.ix_(free, free)]
    F = force[free]
    rows: list[tuple[complex, ...]] = []
    for frequency in frequencies:
        omega = 2 * math.pi * frequency
        # Rayleigh damping is exact for the declared matrix; modal ratios use a
        # diagonal approximation that remains explicit in the result evidence.
        C = (damping.rayleigh_alpha_s or 0.0) * M + (damping.rayleigh_beta_s or 0.0) * K
        if damping.modal_ratios:
            C = C + 2 * damping.modal_ratios[0] * max(omega, 1e-12) * M
        A = K - omega * omega * M + 1j * omega * C
        try:
            reduced = np.linalg.solve(A, F.astype(complex))
        except np.linalg.LinAlgError:
            return FrequencyResponseResult(status="indeterminate", issues=(_issue("RESONANCE-UNRESOLVED", "Frequency response matrix is singular; zero-damping resonance is not assigned a finite response.", op, actual=frequency, unit="Hz"),), model_sha256=model.content_hash, damping=damping)
        full = np.zeros(model.dof_count, dtype=complex)
        full[free] = reduced
        rows.append(tuple(complex(v) for v in full))
    peaks = {dof: float(max(abs(row[i]) for row in rows)) for i, dof in enumerate((model.dof_ids))} if rows else {}
    return FrequencyResponseResult(status="completed", model_sha256=model.content_hash, frequencies_hz=frequencies, response=tuple(rows), peak_amplitude=peaks, damping=damping, evidence={"input_unit": "N", "response_unit": "m", "frequency_count": len(frequencies), "adaptive_refinement": False})


def solve_transient_response(*, model: StructuralModel, times_s: Sequence[float], force_history: Sequence[Sequence[float]], initial_displacement: Sequence[float] | None = None, initial_velocity: Sequence[float] | None = None, damping: DampingSpec = DampingSpec()) -> TransientResult:
    op = "solve_transient_response"
    if model.mass_matrix is None:
        return TransientResult(status="capability_failed", issues=(_issue("MASS-MISSING", "Transient response requires an explicit mass matrix.", op),), model_sha256=model.content_hash)
    times = np.asarray(times_s, dtype=float)
    forces = np.asarray(force_history, dtype=float)
    if times.ndim != 1 or len(times) < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0) or forces.shape != (len(times), model.dof_count) or not np.isfinite(forces).all():
        return TransientResult(status="validation_failed", issues=(_issue("TIME-INVALID", "times_s must be strictly increasing and force_history must match (time, dof).", op),), model_sha256=model.content_hash)
    fixed = set(model.fixed_dofs)
    free = np.array([i for i in range(model.dof_count) if i not in fixed], dtype=int)
    M = np.asarray(model.mass_matrix)[np.ix_(free, free)]
    K = np.asarray(model.stiffness_matrix)[np.ix_(free, free)]
    C = (damping.rayleigh_alpha_s or 0.0) * M + (damping.rayleigh_beta_s or 0.0) * K
    def _initial(value: Sequence[float] | None, name: str) -> np.ndarray:
        if value is None:
            return np.zeros(len(free))
        candidate = np.asarray(value, dtype=float)
        if candidate.shape == (model.dof_count,):
            return candidate[free]
        if candidate.shape == (len(free),):
            return candidate
        raise ValueError(f"{name} must cover all model DOFs or all free DOFs")
    try:
        u0 = _initial(initial_displacement, "initial_displacement")
        v0 = _initial(initial_velocity, "initial_velocity")
    except (TypeError, ValueError):
        return TransientResult(status="validation_failed", issues=(_issue("STATE-INVALID", "Initial displacement/velocity shape does not match the model.", op),), model_sha256=model.content_hash)
    try:
        invM = np.linalg.inv(M)
        def rhs(t: float, y: np.ndarray) -> np.ndarray:
            f = np.array([np.interp(t, times, forces[:, i]) for i in free])
            acc = invM @ (f - C @ y[len(free):] - K @ y[:len(free)])
            return np.concatenate((y[len(free):], acc))
        sol = solve_ivp(rhs, (float(times[0]), float(times[-1])), np.concatenate((u0, v0)), t_eval=times, rtol=1e-7, atol=1e-9)
        if not sol.success:
            return TransientResult(status="indeterminate", issues=(_issue("TRANSIENT-SOLVE-FAILED", sol.message, op),), model_sha256=model.content_hash)
        U = np.zeros((len(times), model.dof_count)); V = np.zeros_like(U); A = np.zeros_like(U)
        U[:, free] = sol.y[:len(free)].T; V[:, free] = sol.y[len(free):].T
        for i, t in enumerate(times):
            f = forces[i, free]
            A[i, free] = invM @ (f - C @ V[i, free] - K @ U[i, free])
        return TransientResult(status="completed", model_sha256=model.content_hash, times_s=tuple(float(v) for v in times), displacement_m=tuple(tuple(float(v) for v in row) for row in U), velocity_m_s=tuple(tuple(float(v) for v in row) for row in V), acceleration_m_s2=tuple(tuple(float(v) for v in row) for row in A), time_step_s=float(np.median(np.diff(times))), evidence={"solver": "scipy.solve_ivp", "internal_steps": "adaptive", "fixed_dofs": list(fixed)})
    except (np.linalg.LinAlgError, ValueError, IndexError) as exc:
        return TransientResult(status="indeterminate", issues=(_issue("TRANSIENT-SOLVE-FAILED", str(exc), op),), model_sha256=model.content_hash)


def estimate_psd(*, times_s: Sequence[float], values: Sequence[float], unit: str, segment_length: int | None = None, overlap: float = 0.5) -> PSDResult:
    op = "estimate_psd"
    t = np.asarray(times_s, dtype=float); x = np.asarray(values, dtype=float)
    if t.ndim != 1 or x.ndim != 1 or len(t) != len(x) or len(t) < 4 or not np.isfinite(t).all() or not np.isfinite(x).all() or np.any(np.diff(t) <= 0):
        return PSDResult(status="validation_failed", issues=(_issue("TIME-INVALID", "PSD estimation requires finite, strictly increasing, equally sampled times and values.", op),), unit=unit, sample_rate_hz=1.0)
    dt = np.diff(t)
    if np.max(dt) - np.min(dt) > max(1e-10, 1e-6 * np.mean(dt)):
        return PSDResult(status="validation_failed", issues=(_issue("TIME-NONUNIFORM", "Welch PSD requires equally sampled data.", op),), unit=unit, sample_rate_hz=1.0)
    if not unit:
        return PSDResult(status="validation_failed", issues=(_issue("UNIT-MISSING", "PSD unit is required.", op),), unit=unit, sample_rate_hz=1.0)
    fs = 1.0 / float(np.mean(dt)); nperseg = int(segment_length or min(256, len(x))); nperseg = max(2, min(nperseg, len(x)))
    noverlap = int(round(nperseg * overlap))
    if not 0 <= overlap < 1:
        return PSDResult(status="validation_failed", issues=(_issue("PSD-INVALID", "overlap must be in [0, 1).", op),), unit=unit, sample_rate_hz=fs)
    f, p = welch(x, fs=fs, nperseg=nperseg, noverlap=noverlap, detrend="constant", return_onesided=True)
    variance = float(np.trapezoid(p, f) if hasattr(np, "trapezoid") else np.trapz(p, f))
    return PSDResult(status="completed", frequency_hz=tuple(float(v) for v in f), psd=tuple(float(v) for v in p), unit=unit, variance=variance, sample_rate_hz=fs, segment_count=max(1, (len(x) - noverlap) // (nperseg - noverlap)), evidence={"window": "Welch-default-Hann", "overlap": overlap, "one_sided": True})


def compute_rms(*, frequency_hz: Sequence[float], psd: Sequence[float], mean: float = 0.0) -> float:
    f = np.asarray(frequency_hz, dtype=float); p = np.asarray(psd, dtype=float)
    if f.ndim != 1 or p.shape != f.shape or len(f) < 2 or np.any(~np.isfinite(f)) or np.any(~np.isfinite(p)) or np.any(p < 0) or np.any(np.diff(f) <= 0):
        raise ValueError("frequency_hz and psd must be finite, increasing, nonnegative arrays of equal length")
    integral = float(np.trapezoid(p, f) if hasattr(np, "trapezoid") else np.trapz(p, f))
    return math.sqrt(max(0.0, integral + float(mean) ** 2))


def check_resonance_margin(*, natural_frequencies_hz: Sequence[float], excitation_frequencies_hz: Sequence[float], minimum_margin_hz: float, damping_ratio: float = 0.0) -> PhysicsReport:
    op = "check_resonance_margin"
    margin = _positive(minimum_margin_hz, "minimum_margin_hz", op)
    damping = _finite(damping_ratio, "damping_ratio", op)
    if damping < 0:
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("DAMPING-INVALID", "damping_ratio cannot be negative.", op),))
    natural = tuple(_finite(v, "natural_frequency", op) for v in natural_frequencies_hz); excitation = tuple(_finite(v, "excitation_frequency", op) for v in excitation_frequencies_hz)
    if not natural or not excitation:
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("FREQUENCY-MISSING", "Both natural and excitation frequencies are required.", op),))
    closest = min(abs(a - b) for a in natural for b in excitation)
    passed = closest >= margin or damping > 0.2
    return PhysicsReport(operation=op, status="passed" if passed else "failed", issues=() if passed else (_issue("RESONANCE-MARGIN-LOW", "Excitation lies within the declared resonance margin.", op, actual=closest, expected=margin, unit="Hz"),), evidence={"closest_margin_hz": closest, "minimum_margin_hz": margin, "damping_ratio": damping})


def check_vibration_limits(*, values: Sequence[float], limit: float, metric: str = "peak", unit: str = "") -> PhysicsReport:
    op = "check_vibration_limits"
    bound = _positive(limit, "limit", op)
    samples = tuple(_finite(v, "value", op) for v in values)
    if not samples:
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("VIBRATION-MISSING", "At least one vibration value is required.", op),))
    actual = max(abs(v) for v in samples)
    status = "passed" if actual <= bound else "failed"
    return PhysicsReport(operation=op, status=status, issues=() if status == "passed" else (_issue("VIBRATION-LIMIT-EXCEEDED", "Vibration value exceeds the declared limit.", op, actual=actual, expected=bound, unit=unit or None),), evidence={"metric": metric, "actual": actual, "limit": bound, "unit": unit})


__all__ = ["ModalRequest", "DampingSpec", "ModalResult", "FrequencyResponseResult", "TransientResult", "RandomLoadSpec", "PSDResult", "solve_modes", "solve_frequency_response", "solve_transient_response", "estimate_psd", "compute_rms", "check_resonance_margin", "check_vibration_limits"]
