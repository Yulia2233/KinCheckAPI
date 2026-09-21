"""Linear structural reference calculations for KinCheckAPI 0.6.4.

The module deliberately accepts an explicit reduced finite-element model rather
than pretending that a CAD BREP is a structural mesh.  It provides deterministic
matrix and Euler--Bernoulli reference calculations, load-transfer accounting,
and checks that can be attached to a future CalculiX/FEA adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import eigh

from .diagnostics import Evidence, SimIssue
from .physics_types import PhysicsReport, digest, fail, issue, plain


def _finite(value: Any, name: str, operation: str) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = math.nan
    if not math.isfinite(value):
        fail("VALUE-INVALID", f"{name} must be finite.", operation=operation)
    return value


def _positive(value: Any, name: str, operation: str) -> float:
    value = _finite(value, name, operation)
    if value <= 0:
        fail("VALUE-INVALID", f"{name} must be positive.", operation=operation)
    return value


def _matrix(value: Any, name: str, operation: str, *, symmetric: bool = False) -> tuple[tuple[float, ...], ...]:
    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        matrix = np.empty((0, 0))
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not matrix.size or not np.isfinite(matrix).all():
        fail("MATRIX-INVALID", f"{name} must be a finite nonempty square matrix.", operation=operation)
    if symmetric and not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12):
        fail("MATRIX-INVALID", f"{name} must be symmetric.", operation=operation)
    return tuple(tuple(float(v) for v in row) for row in matrix)


def _issue(code: str, message: str, operation: str, objects: Sequence[str] = (), **kwargs: Any) -> SimIssue:
    return issue(code, message, operation, tuple(objects), **kwargs)


@dataclass(frozen=True, slots=True, kw_only=True)
class ElasticMaterial:
    material_id: str
    youngs_modulus_pa: float
    poisson_ratio: float
    density_kg_m3: float
    source: str
    yield_strength_pa: float | None = None
    ultimate_strength_pa: float | None = None

    def __post_init__(self) -> None:
        op = "ElasticMaterial"
        if not self.material_id or not self.source:
            fail("MATERIAL-MISSING", "Material identity and source are required.", operation=op)
        object.__setattr__(self, "youngs_modulus_pa", _positive(self.youngs_modulus_pa, "youngs_modulus_pa", op))
        nu = _finite(self.poisson_ratio, "poisson_ratio", op)
        if not -1.0 < nu < 0.5:
            fail("MATERIAL-INVALID", "poisson_ratio must be between -1 and 0.5.", operation=op)
        object.__setattr__(self, "poisson_ratio", nu)
        object.__setattr__(self, "density_kg_m3", _positive(self.density_kg_m3, "density_kg_m3", op))
        for name in ("yield_strength_pa", "ultimate_strength_pa"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _positive(value, name, op))

    @property
    def shear_modulus_pa(self) -> float:
        return self.youngs_modulus_pa / (2.0 * (1.0 + self.poisson_ratio))

    def to_dict(self) -> dict[str, Any]:
        return plain(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class FailureCriterion:
    name: str = "von_mises"
    allowable_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.name not in ("von_mises", "maximum_normal", "tresca"):
            fail("CRITERION-UNSUPPORTED", f"Unsupported failure criterion {self.name!r}.", operation="FailureCriterion")
        object.__setattr__(self, "allowable_factor", _positive(self.allowable_factor, "allowable_factor", "FailureCriterion"))


@dataclass(frozen=True, slots=True, kw_only=True)
class StructuralLoad:
    load_id: str
    values: tuple[float, ...]
    target_dofs: tuple[int, ...] = ()
    source: str = "explicit"
    time_s: float | None = None

    def __post_init__(self) -> None:
        if not self.load_id or not self.source:
            fail("LOAD-INVALID", "Structural load requires an ID and source.", operation="StructuralLoad")
        values = tuple(_finite(v, "load", "StructuralLoad") for v in self.values)
        if not values:
            fail("LOAD-INVALID", "Structural load values cannot be empty.", operation="StructuralLoad")
        object.__setattr__(self, "values", values)
        target = tuple(int(i) for i in self.target_dofs)
        if target and len(values) != len(target):
            fail("LOAD-INVALID", "values and target_dofs must have equal lengths.", operation="StructuralLoad")
        if any(i < 0 for i in target):
            fail("LOAD-INVALID", "target_dofs must be nonnegative.", operation="StructuralLoad")
        object.__setattr__(self, "target_dofs", target)
        if self.time_s is not None:
            object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", "StructuralLoad"))


@dataclass(frozen=True, slots=True, kw_only=True)
class StructuralModel:
    model_id: str
    stiffness_matrix: tuple[tuple[float, ...], ...]
    mass_matrix: tuple[tuple[float, ...], ...] | None = None
    dof_ids: tuple[str, ...] = ()
    fixed_dofs: tuple[int, ...] = ()
    material: ElasticMaterial | None = None
    length_m: float | None = None
    area_m2: float | None = None
    second_moment_m4: float | None = None
    polar_moment_m4: float | None = None
    mesh_hash: str | None = None
    mesh_quality: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        op = "StructuralModel"
        if not self.model_id:
            fail("MODEL-INVALID", "model_id is required.", operation=op)
        k = _matrix(self.stiffness_matrix, "stiffness_matrix", op, symmetric=True)
        object.__setattr__(self, "stiffness_matrix", k)
        n = len(k)
        if self.mass_matrix is not None:
            m = _matrix(self.mass_matrix, "mass_matrix", op, symmetric=True)
            if len(m) != n:
                fail("MATRIX-INVALID", "mass_matrix and stiffness_matrix dimensions must match.", operation=op)
            if np.min(np.linalg.eigvalsh(np.asarray(m))) <= 0:
                fail("MATRIX-INVALID", "mass_matrix must be positive definite.", operation=op)
            object.__setattr__(self, "mass_matrix", m)
        object.__setattr__(self, "dof_ids", tuple(self.dof_ids) if self.dof_ids else tuple(f"dof_{i}" for i in range(n)))
        if len(self.dof_ids) != n or len(set(self.dof_ids)) != n:
            fail("DOF-INVALID", "dof_ids must cover every matrix row exactly once.", operation=op)
        fixed = tuple(int(i) for i in self.fixed_dofs)
        if any(i < 0 or i >= n for i in fixed) or len(set(fixed)) != len(fixed):
            fail("BOUNDARY-INVALID", "fixed_dofs must be unique valid matrix indices.", operation=op)
        object.__setattr__(self, "fixed_dofs", fixed)
        for name in ("length_m", "area_m2", "second_moment_m4", "polar_moment_m4"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _positive(value, name, op))
        object.__setattr__(self, "mesh_quality", {str(k): _finite(v, str(k), op) for k, v in self.mesh_quality.items()})

    @property
    def dof_count(self) -> int:
        return len(self.stiffness_matrix)

    @property
    def content_hash(self) -> str:
        payload = plain(self)
        return digest(payload)

    def to_dict(self) -> dict[str, Any]:
        return {**plain(self), "content_hash": self.content_hash}


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadTransferMap:
    source_id: str
    target_dofs: tuple[int, ...]
    force_components: tuple[float, ...]
    reference_point_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    coordinate_frame: str = "world"

    def __post_init__(self) -> None:
        if not self.source_id:
            fail("LOAD-MAP-INVALID", "source_id is required.", operation="LoadTransferMap")
        if len(self.target_dofs) != len(self.force_components) or not self.target_dofs:
            fail("LOAD-MAP-INVALID", "target_dofs and force_components must have equal nonzero length.", operation="LoadTransferMap")
        target = tuple(int(i) for i in self.target_dofs)
        if any(i < 0 for i in target):
            fail("LOAD-MAP-INVALID", "target_dofs must be nonnegative.", operation="LoadTransferMap")
        object.__setattr__(self, "target_dofs", target)
        object.__setattr__(self, "force_components", tuple(_finite(v, "force_component", "LoadTransferMap") for v in self.force_components))
        object.__setattr__(self, "reference_point_m", tuple(_finite(v, "reference_point_m", "LoadTransferMap") for v in self.reference_point_m))


@dataclass(frozen=True, slots=True, kw_only=True)
class StructuralResult(PhysicsReport):
    operation: str = "solve_static_structure"
    model_sha256: str | None = None
    displacements_m: Mapping[str, float] = field(default_factory=dict)
    reactions_n: Mapping[str, float] = field(default_factory=dict)
    stresses_pa: Mapping[str, float] = field(default_factory=dict)
    strains: Mapping[str, float] = field(default_factory=dict)
    load_resultant: tuple[float, ...] = ()
    residual_norm: float = 0.0
    converged: bool = False
    roi: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        for name in ("displacements_m", "reactions_n", "stresses_pa", "strains"):
            object.__setattr__(self, name, {str(k): _finite(v, name, "StructuralResult") for k, v in getattr(self, name).items()})
        object.__setattr__(self, "residual_norm", _finite(self.residual_norm, "residual_norm", "StructuralResult"))
        object.__setattr__(self, "load_resultant", tuple(_finite(v, "load_resultant", "StructuralResult") for v in self.load_resultant))
        if self.status in ("completed", "completed_with_warnings") and not self.displacements_m:
            fail("RESULT-INCOMPLETE", "Completed structural result requires displacements.", operation="StructuralResult")


@dataclass(frozen=True, slots=True, kw_only=True)
class BucklingResult(PhysicsReport):
    operation: str = "solve_buckling_screening"
    model_sha256: str | None = None
    eigenvalues: tuple[float, ...] = ()
    mode_shapes: tuple[tuple[float, ...], ...] = ()
    reference_load_n: float = 0.0
    converged: bool = False

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "eigenvalues", tuple(_finite(v, "eigenvalue", self.operation) for v in self.eigenvalues))
        object.__setattr__(self, "mode_shapes", tuple(tuple(_finite(v, "mode_shape", self.operation) for v in row) for row in self.mode_shapes))
        object.__setattr__(self, "reference_load_n", _finite(self.reference_load_n, "reference_load_n", self.operation))


def transfer_loads(*, model: StructuralModel, loads: Sequence[StructuralLoad] = (), maps: Sequence[LoadTransferMap] = ()) -> tuple[np.ndarray, PhysicsReport]:
    """Assemble loads into the model vector and prove force bookkeeping."""
    op = "transfer_loads"
    vector = np.zeros(model.dof_count, dtype=float)
    records: list[dict[str, Any]] = []
    maps_by_source = {item.source_id: item for item in maps}
    issues: list[SimIssue] = []
    for load in loads:
        mapping = maps_by_source.get(load.load_id)
        if mapping is None:
            if load.target_dofs:
                mapping = LoadTransferMap(source_id=load.load_id, target_dofs=load.target_dofs, force_components=load.values)
            else:
                issues.append(_issue("LOAD-MAP-MISSING", "Load has no target DOF mapping.", op, (load.load_id,)))
                continue
        if any(i >= model.dof_count for i in mapping.target_dofs):
            issues.append(_issue("LOAD-MAP-INVALID", "Load target exceeds structural model DOFs.", op, (load.load_id,)))
            continue
        if len(mapping.force_components) != len(mapping.target_dofs):
            issues.append(_issue("LOAD-MAP-INVALID", "Load mapping component count does not match target DOFs.", op, (load.load_id,)))
            continue
        for dof, value in zip(mapping.target_dofs, mapping.force_components):
            vector[dof] += value
        records.append({"load_id": load.load_id, "source": load.source, "target_dofs": list(mapping.target_dofs), "values": list(mapping.force_components)})
    status = "passed" if not issues else "validation_failed"
    return vector, PhysicsReport(operation=op, status=status, issues=tuple(issues), evidence={"load_records": records, "resultant": vector.tolist()})


def solve_static_structure(*, model: StructuralModel, loads: Sequence[StructuralLoad] = (), load_vector: Sequence[float] | None = None, fixed_dofs: Sequence[int] | None = None, maps: Sequence[LoadTransferMap] = (), roi: Sequence[str] = ()) -> StructuralResult:
    """Solve K u = f for a declared linear model with explicit supports."""
    op = "solve_static_structure"
    fixed = model.fixed_dofs if fixed_dofs is None else tuple(int(i) for i in fixed_dofs)
    if any(i < 0 or i >= model.dof_count for i in fixed):
        return StructuralResult(status="validation_failed", issues=(_issue("BOUNDARY-INVALID", "A fixed DOF is outside the structural model.", op),), model_sha256=model.content_hash)
    if load_vector is None:
        vector, report = transfer_loads(model=model, loads=loads, maps=maps)
        if not report.passed:
            return StructuralResult(status="validation_failed", issues=report.issues, model_sha256=model.content_hash)
    else:
        try:
            vector = np.asarray(load_vector, dtype=float)
        except (TypeError, ValueError):
            vector = np.empty(0)
        if vector.shape != (model.dof_count,) or not np.isfinite(vector).all():
            return StructuralResult(status="validation_failed", issues=(_issue("LOAD-INVALID", "load_vector must match the structural DOF count and be finite.", op),), model_sha256=model.content_hash)
    K = np.asarray(model.stiffness_matrix, dtype=float)
    free = np.array([i for i in range(model.dof_count) if i not in fixed], dtype=int)
    if free.size == 0:
        return StructuralResult(status="validation_failed", issues=(_issue("BOUNDARY-INVALID", "All DOFs are fixed; no structural response can be solved.", op),), model_sha256=model.content_hash)
    try:
        Kff = K[np.ix_(free, free)]
        cond = float(np.linalg.cond(Kff))
        if not math.isfinite(cond) or cond > 1e12:
            return StructuralResult(status="indeterminate", issues=(_issue("MATRIX-SINGULAR", "Free structural stiffness is singular or ill-conditioned.", op, actual=cond, expected="<= 1e12"),), model_sha256=model.content_hash)
        eigenvalues = np.linalg.eigvalsh(Kff)
        if eigenvalues[0] <= max(abs(eigenvalues[-1]) * 1e-12, 1e-15):
            return StructuralResult(status="indeterminate", issues=(_issue("STIFFNESS-NOT-POSITIVE", "Free structural stiffness must be positive definite for a stable linear static solve.", op, actual=float(eigenvalues[0]), expected="> 0", unit="N/m"),), model_sha256=model.content_hash)
        u = np.zeros(model.dof_count, dtype=float)
        u[free] = np.linalg.solve(Kff, vector[free])
        full_residual = K @ u - vector
        residual = full_residual[free]
        reactions = full_residual
    except np.linalg.LinAlgError as exc:
        return StructuralResult(status="indeterminate", issues=(_issue("MATRIX-SINGULAR", str(exc), op),), model_sha256=model.content_hash)
    stresses: dict[str, float] = {}
    strains: dict[str, float] = {}
    if model.length_m and model.area_m2 and model.material:
        axial = float(np.max(np.abs(vector)))
        stress = axial / model.area_m2
        stresses["axial"] = stress
        strains["axial"] = stress / model.material.youngs_modulus_pa
    evidence = {"backend": "kincheck-linear-reference", "condition_number": cond, "load_vector": vector.tolist(), "fixed_dofs": list(fixed), "residual_norm": float(np.linalg.norm(residual)), "support_reactions": {model.dof_ids[i]: float(reactions[i]) for i in fixed}, "mesh_hash": model.mesh_hash, "roi": list(roi)}
    return StructuralResult(status="completed", model_sha256=model.content_hash, displacements_m={dof: float(u[i]) for i, dof in enumerate(model.dof_ids)}, reactions_n={dof: float(reactions[i]) for i, dof in enumerate(model.dof_ids) if i in fixed}, stresses_pa=stresses, strains=strains, load_resultant=tuple(float(v) for v in vector), residual_norm=float(np.linalg.norm(residual)), converged=True, roi=tuple(roi), evidence=evidence)


def solve_buckling_screening(*, model: StructuralModel, compressive_load_n: float | None = None, mode_count: int = 3, effective_length_factor: float = 1.0, geometric_stiffness_matrix: Sequence[Sequence[float]] | None = None) -> BucklingResult:
    """Return generalized eigenvalue screening or Euler load for a beam model."""
    op = "solve_buckling_screening"
    if mode_count < 1 or effective_length_factor <= 0:
        return BucklingResult(status="validation_failed", issues=(_issue("VALUE-INVALID", "mode_count and effective_length_factor must be positive.", op),), model_sha256=model.content_hash)
    if compressive_load_n is not None and compressive_load_n <= 0:
        return BucklingResult(status="validation_failed", issues=(_issue("LOAD-INVALID", "compressive_load_n must be positive.", op),), model_sha256=model.content_hash)
    if model.length_m and model.second_moment_m4 and model.material:
        base = math.pi**2 * model.material.youngs_modulus_pa * model.second_moment_m4 / (effective_length_factor * model.length_m) ** 2
        eigenvalues = tuple(base * n * n for n in range(1, mode_count + 1))
        evidence = {"method": "euler-column-screening", "effective_length_m": effective_length_factor * model.length_m, "assumptions": ["small deflection", "linear elastic", "declared end-condition factor"]}
    elif geometric_stiffness_matrix is not None:
        try:
            free = np.array([i for i in range(model.dof_count) if i not in model.fixed_dofs], dtype=int)
            K = np.asarray(model.stiffness_matrix)[np.ix_(free, free)]
            G_full = np.asarray(_matrix(geometric_stiffness_matrix, "geometric_stiffness_matrix", op, symmetric=True), dtype=float)
            if G_full.shape != np.asarray(model.stiffness_matrix).shape:
                return BucklingResult(status="validation_failed", issues=(_issue("MATRIX-INVALID", "geometric_stiffness_matrix must match stiffness_matrix dimensions.", op),), model_sha256=model.content_hash)
            G = G_full[np.ix_(free, free)]
            if np.min(np.linalg.eigvalsh(G)) <= 0:
                return BucklingResult(status="validation_failed", issues=(_issue("MATRIX-INVALID", "geometric_stiffness_matrix must be positive definite on free DOFs.", op),), model_sha256=model.content_hash)
            values, vectors = eigh(K, G)
            values = np.maximum(values[:mode_count], 0.0)
            reference = float(compressive_load_n or 1.0)
            return BucklingResult(status="completed", model_sha256=model.content_hash, eigenvalues=tuple(float(v) for v in values), mode_shapes=tuple(tuple(float(x) for x in vectors[:, i]) for i in range(len(values))), reference_load_n=reference, converged=True, evidence={"method": "linearized-eigenvalue-screening", "reference_load_n": reference, "critical_loads_n": [float(v * reference) for v in values]})
        except Exception as exc:
            return BucklingResult(status="indeterminate", issues=(_issue("BUCKLING-SOLVE-FAILED", str(exc), op),), model_sha256=model.content_hash)
    else:
        return BucklingResult(status="capability_failed", issues=(_issue("GEOMETRIC-STIFFNESS-MISSING", "Matrix buckling screening requires an explicit geometric stiffness matrix; a mass matrix cannot substitute for it.", op),), model_sha256=model.content_hash)
    reference = float(compressive_load_n or 1.0)
    return BucklingResult(status="completed", model_sha256=model.content_hash, eigenvalues=eigenvalues, reference_load_n=reference, converged=True, evidence=evidence)


def check_stress(*, result: StructuralResult, allowable_stress_pa: float | None = None, material: ElasticMaterial | None = None, criterion: FailureCriterion = FailureCriterion()) -> PhysicsReport:
    op = "check_stress"
    if result.status not in ("completed", "completed_with_warnings") or not result.converged or any(item.severity == "error" for item in result.issues):
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("RESULT-UNRESOLVED", "Stress checks require a completed, converged structural result without errors.", op),), evidence={"result_status": result.status, "converged": result.converged})
    allowable = allowable_stress_pa if allowable_stress_pa is not None else (material.yield_strength_pa if material else None)
    if allowable is None or allowable <= 0:
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("ALLOWABLE-MISSING", "A positive allowable or material yield strength is required.", op),), evidence={"stress_pa": dict(result.stresses_pa)})
    max_stress = max((abs(v) for v in result.stresses_pa.values()), default=math.nan)
    if not math.isfinite(max_stress):
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("STRESS-MISSING", "Structural result has no stress evidence.", op),))
    utilization = max_stress / (allowable / criterion.allowable_factor)
    status = "passed" if utilization <= 1.0 else "failed"
    issues = () if status == "passed" else (_issue("STRESS-LIMIT-EXCEEDED", "Structural stress exceeds the declared allowable.", op, actual=max_stress, expected=allowable, unit="Pa"),)
    return PhysicsReport(operation=op, status=status, issues=issues, evidence={"max_stress_pa": max_stress, "allowable_pa": allowable, "utilization": utilization, "criterion": criterion.name})


def check_deflection(*, result: StructuralResult, allowable_displacement_m: float) -> PhysicsReport:
    op = "check_deflection"
    if result.status not in ("completed", "completed_with_warnings") or not result.converged or any(item.severity == "error" for item in result.issues):
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("RESULT-UNRESOLVED", "Deflection checks require a completed, converged structural result without errors.", op),), evidence={"result_status": result.status, "converged": result.converged})
    allowable = _positive(allowable_displacement_m, "allowable_displacement_m", op)
    maximum = max((abs(v) for v in result.displacements_m.values()), default=math.nan)
    if not math.isfinite(maximum):
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("DISPLACEMENT-MISSING", "Structural result has no displacement evidence.", op),))
    utilization = maximum / allowable
    status = "passed" if utilization <= 1 else "failed"
    return PhysicsReport(operation=op, status=status, issues=() if status == "passed" else (_issue("DEFLECTION-LIMIT-EXCEEDED", "Structural displacement exceeds the declared limit.", op, actual=maximum, expected=allowable, unit="m"),), evidence={"max_displacement_m": maximum, "allowable_m": allowable, "utilization": utilization})


def check_structural_margin(*, result: StructuralResult, allowable_stress_pa: float | None = None, material: ElasticMaterial | None = None, allowable_displacement_m: float | None = None) -> PhysicsReport:
    checks = [check_stress(result=result, allowable_stress_pa=allowable_stress_pa, material=material)]
    if allowable_displacement_m is not None:
        checks.append(check_deflection(result=result, allowable_displacement_m=allowable_displacement_m))
    issues = tuple(item for check in checks for item in check.issues)
    status = "passed" if all(check.passed for check in checks) else ("indeterminate" if any(check.status == "indeterminate" for check in checks) else "failed")
    return PhysicsReport(operation="check_structural_margin", status=status, issues=issues, evidence={"checks": [check.to_dict() for check in checks]})


__all__ = ["ElasticMaterial", "FailureCriterion", "StructuralLoad", "StructuralModel", "LoadTransferMap", "StructuralResult", "BucklingResult", "transfer_loads", "solve_static_structure", "solve_buckling_screening", "check_stress", "check_deflection", "check_structural_margin"]
