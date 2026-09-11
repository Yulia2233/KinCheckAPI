#!/usr/bin/env python3
"""Generate the English skill API reference from the public runtime surface."""

from __future__ import annotations

import argparse
import dataclasses
import enum
import importlib
import inspect
from pathlib import Path
import types
from typing import Any

import generate_skill_api_docs as source


REPO_ROOT = Path(__file__).resolve().parents[1]


MODULES: dict[str, dict[str, str]] = {
    "cadir": {
        "title": "CADIR Input Conversion",
        "summary": "Read CADIR-exported MJCF, mapping, and mesh assets and construct a verifiable assembly model.",
    },
    "assembly": {
        "title": "Assembly Model and Topology",
        "summary": "Define immutable assembly objects, construct part and component relationships, and validate kinematic topology.",
    },
    "scenario": {
        "title": "Scenarios and Drivers",
        "summary": "Define initial state, drivers, run duration, sampling, and result recording scope.",
    },
    "kinematics": {
        "title": "Kinematic Solving and Analysis",
        "summary": "Solve positions and continuous motion and analyze degrees of freedom, Jacobians, singularities, and workspaces.",
    },
    "checks": {
        "title": "Acceptance Checks",
        "summary": "Turn user claims into structured, reviewable kinematic acceptance checks.",
        "exports": ("CheckReport", "CheckSpec", "CheckSuiteReport", "CheckType", "Direction", "RatioMeasurement", "AssemblyIntegrityReport", "ContainmentRelation", "IntegrityRelationResult", "check_assembly_integrity", "check_constraint_equation_residuals", "check_constraint_residuals", "check_joint_limits", "check_interference", "check_minimum_clearance", "check_motion_envelope", "check_pose_target", "check_trajectory", "check_transmission_ratio", "run_checks"),
    },
    "clearance": {
        "title": "Geometric Safety",
        "summary": "Check mesh interference, minimum clearance, and motion envelopes at discrete motion samples.",
    },
    "result": {
        "title": "Result Models and Queries",
        "summary": "Read status, trajectories, residuals, and event evidence from MotionResult objects.",
    },
    "diagnostics": {
        "title": "Structured Diagnostics",
        "summary": "Collect, explain, and persist stable error codes, evidence, and failure context.",
    },
    "errors": {
        "title": "Public Exceptions",
        "summary": "Define the stable KinCheckAPI exception hierarchy that callers can catch, serialize, and report.",
    },
    "export": {
        "title": "Result Packages",
        "summary": "Write, validate, and read backend-independent .kincheck motion result packages.",
    },
    "pose": {
        "title": "Pose Operations",
        "summary": "Perform rigid-body pose operations using SI units and xyzw quaternion ordering.",
    },
    "trajectory_checks": {
        "title": "Trajectory Utilities",
        "summary": "Compute trajectory-window metrics and filter joint-limit events.",
    },
    "visualization": {
        "title": "Offline Visualization",
        "summary": "Export public motion results and meshes as an offline Three.js viewer.",
    },
    "kinematics_conventions": {
        "title": "Kinematic Coordinate Conventions",
        "summary": "Define stable sign conventions between authored connector order and motion-tree propagation direction.",
    },
    "kinematics_geometry": {
        "title": "Low-Level Kinematic Geometry",
        "summary": "Provide backend-independent pose propagation, Jacobian, mobility, and position-solving primitives.",
    },
    "kinematics_limits": {
        "title": "Joint-Limit Events",
        "summary": "Determine the first reached or exceeded event from assembly limits and joint trajectories.",
    },
    "dynamics": {
        "title": "Dynamics Namespace",
        "summary": "Reserved dynamics namespace; v0.5.0 exposes no public dynamics operations.",
    },
}


MODULE_RULES: dict[str, tuple[str, ...]] = {
    "cadir": (
        "The XML root `model` must be non-empty and equal the mapping `root_definition_id`.",
        "XML, mapping, and meshes must come from the same export batch; asset resolution must not escape `asset_root`.",
        "Conversion returns an assembly model and source map; it does not replace assembly, topology, or Scenario validation.",
    ),
    "assembly": (
        "The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.",
        "IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.",
        "Run `validate_assembly()` and `validate_topology()` before solving.",
    ),
    "scenario": (
        "Scenario is immutable; every configuration function returns a new object.",
        "Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.",
        "Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.",
    ),
    "kinematics": (
        "Validate the assembly and Scenario before solving or analysis.",
        "Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.",
        "Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.",
    ),
    "checks": (
        "Each check must identify its objects, time window, expected value, threshold, and units.",
        "A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.",
        "Read `CheckReport.passed` together with evidence, issues, and metadata.",
        "Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.",
        "Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.",
    ),
    "clearance": (
        "Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.",
        "Results come from triangle meshes and discrete time samples; they are not continuous-time collision proofs.",
        "Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.",
    ),
    "result": (
        "Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.",
        "Query times must lie within the result range, and interpolated evidence must retain the original sampling range.",
        "Inspect status, sample count, and issues before using trajectories, residuals, or events.",
    ),
    "diagnostics": (
        "Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.",
        "Execute an automatic fix only when a public API defines it and its preconditions are verifiable.",
        "Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.",
    ),
    "errors": (
        "Catch `KinCheckError` for expected domain failures, then narrow to subclasses when needed.",
        "Preserve `code`, `report`, `object_ids`, `source_paths`, and `suggested_actions`.",
        "Do not choose repair behavior by matching exception message text.",
    ),
    "export": (
        "Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.",
        "Validate member paths, schemas, hashes, and cross-file references before reading.",
        "With `require_meshes=True`, fail when any required mesh is missing.",
    ),
    "pose": (
        "Use metres for positions and xyzw quaternion ordering.",
        "Input vectors and quaternions must be finite; zero-norm quaternions are invalid.",
        "State the reference frame for parent, child, actual, and expected values.",
    ),
    "trajectory_checks": (
        "The time window must lie in the actual sample range and contain enough samples.",
        "Do not interpret empty windows or invalid position bounds as a pass.",
        "Path length and bounds are derived from discrete samples.",
    ),
    "visualization": (
        "Visualization consumes only public AssemblyModel and MotionResult data, not private backend state.",
        "Inspect motion status, recorded trajectories, and mesh assets before export.",
        "Use the viewer to review evidence, not as a replacement for numerical acceptance checks.",
    ),
    "kinematics_conventions": (
        "Interpret the public joint scalar direction as `component_b - component_a`.",
        "Tree propagation may reverse authored connector order; use this module to convert the sign.",
        "Never infer sign from component names or tree traversal order.",
    ),
    "kinematics_geometry": (
        "These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.",
        "Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.",
        "Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.",
    ),
    "kinematics_limits": (
        "Event detection consumes actual joint trajectories and limits authored in the assembly.",
        "Missing limits or trajectories produce no events and do not establish a limit-check pass.",
        "Tolerance must be finite and non-negative.",
    ),
    "dynamics": (
        "Do not call or invent dynamics APIs in this release.",
        "Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.",
        "Report dynamics requests as outside the current capability boundary.",
    ),
}


PURPOSE_OVERRIDES: dict[str, str] = {
    "convert_mjcf": "Convert CADIR MJCF XML, mapping JSON, and mesh assets into an `AdapterResult`. Canonical `mesh_constraints` preserve gear/belt endpoint frames and SI radii as existing native Constraints, including carrier-relative multi-coordinate equations. Explicit coaxial joint aliases are retained in the source map. Legacy two-joint Coupling conversion remains supported; optional product-package preparation is provided by `kincheckapi.addon`.",
    "build_kinematic_tree": "Analyze rigid groups, motion-tree edges, closure edges, ground, and disconnected islands; this is topology analysis, not motion solving.",
    "validate_assembly": "Aggregate consistency checks for assembly IDs, references, endpoints, ground, joints, constraints, closures, and couplings.",
    "validate_topology": "Validate motion-graph boundaries, connectivity, ground, tree edges, and closure edges before solving.",
    "solve_motion": "Solve continuous kinematic motion over a Scenario time window and return a backend-independent `MotionResult`.",
    "try_solve_motion": "Retain a structured report and `last_valid_result` after failure; never convert failure into a pass.",
    "run_checks": "Execute explicit acceptance claims in `CheckSpec` order and return a `CheckSuiteReport`.",
    "check_interference": "Check specified component pairs for mesh penetration at discrete motion samples.",
    "measure_minimum_clearance": "Measure minimum signed clearance for specified component pairs at discrete motion samples.",
    "create_motion_envelope": "Create a discrete motion envelope for specified components for later spatial interference analysis.",
    "write_motion_result": "Write a complete public motion result as deterministic JSON.",
    "export_motion_package": "Write the assembly, motion result, validation information, and optional meshes to a `.kincheck` file.",
    "motion_package": "Public compatibility alias for `export_motion_package()`.",
    "export_motion_viewer": "Export motion playback assets for an offline Three.js viewer.",
    "verify_transmission_ratio": "Deprecated compatibility entry point; new code must use `kincheckapi.checks.check_transmission_ratio()`.",
    "check_envelope_interference": "Compare world-axis-aligned bounds from two motion-envelope reports; this does not perform triangle-mesh interference or confirm penetration.",
    "set_component_result_scope": "Select component trajectory recording scope. `all` always records all components; `requested` records requested objects when the list is non-empty and preserves the historical all-components behavior when empty.",
    "list_executable_fixes": "Return fixes that a public API can execute safely; v0.5.0 currently always returns an empty tuple.",
    "apply_assembly_fix": "Reserved automatic-fix entry point; v0.5.0 is unimplemented and raises `BackendCapabilityError`.",
    "apply_scenario_fix": "Reserved automatic-fix entry point; v0.5.0 is unimplemented and raises `BackendCapabilityError`.",
    "compute_jacobian": "Compute a backend-independent six-dimensional finite-difference Jacobian for a component or connector at given joint positions.",
    "analyze_mobility": "Analyze effective mechanism degrees of freedom from nominal joint DOFs and constraint Jacobian rank.",
    "detect_limit_events": "Find the first reached or exceeded event for each modeled joint-limit side from actual trajectories.",
    "child_motion_sign": "Convert the public joint coordinate into the motion sign of the current motion-tree child group.",
    "assert_check_passed": "Require a structured check to pass; otherwise raise `VerificationError` while preserving the original check.",
    "collect_issues": "Collect and content-deduplicate `SimIssue` objects from multiple structured results.",
    "create_report": "Combine issues from assembly, Scenario, motion, geometric safety, and checks into one `DiagnosticReport`.",
    "create_backend_failure_report": "Sanitize an unknown backend exception and optional partial result into a stable `DiagnosticReport`.",
    "explain_issue": "Expand one stable `SimIssue` into cause, impact, evidence, and suggested actions.",
    "format_report_for_agent": "Compatibility name that delegates to the single Agent result renderer and accepts no style parameter.",
    "format_result_for_agent": "Format any public validation result and accept no style parameter.",
    "format_error_for_agent": "Format a structured public KinCheckAPI error for an Agent.",
    "write_report": "Write a complete `DiagnosticReport` as deterministic JSON.",
    "compose_pose": "Compose a parent pose with a child pose expressed in the parent frame.",
    "inverse_pose": "Return the inverse rigid transform.",
    "relative_pose": "Return the child pose relative to the parent frame.",
    "rotate_vector": "Rotate a vector using pose orientation without applying translation.",
    "transform_point": "Transform a local point into the parent frame through a pose.",
    "orientation_error_rad": "Compute the shortest unsigned angular error between two orientations in radians.",
    "trajectory_window_metrics": "Compute sample indices, path length, and world-coordinate bounds for one component or connector trajectory over an explicit window.",
    "normalize_position_bounds": "Normalize optional position bounds into a read-only per-axis `(lower, upper)` mapping and reject invalid bounds.",
    "limit_events_in_window": "Filter recorded `LimitEvent` objects by joint ID and time window.",
    "read_joint_state": "Read or interpolate joint position, velocity, and acceleration at a specified time.",
    "read_component_pose": "Read or interpolate a component world pose at a specified time.",
    "read_component_state": "Read a component world pose and the available linear and angular motion values.",
    "read_connector_state": "Read a specified connector world pose and available spatial motion state.",
    "read_trajectory": "Return a complete component or connector trajectory already recorded in the result.",
    "summarize_motion": "Summarize status, duration, sample count, joint extrema, maximum residuals, and event counts.",
    "validate_package": "Validate `.kincheck` member paths, schemas, hashes, and cross-file references and return an aggregate validation result.",
    "read_package": "Strictly validate and reconstruct a `.kincheck` package; raise `MotionPackageError` on failure.",
    "ground_component": "Mark an existing component as fixed in the assembly reference frame and return a new assembly.",
    "exclude_collision_pair": "Add two distinct existing components to the collision exclusion set; this changes later geometric acceptance scope.",
    "assembly_to_dict": "Convert AssemblyModel into a deterministic JSON-compatible dictionary.",
    "assembly_from_dict": "Reconstruct AssemblyModel from a parsed mapping; assembly and topology validation are still required.",
    "scenario_to_dict": "Convert Scenario into a deterministic JSON-compatible dictionary.",
    "scenario_from_dict": "Reconstruct a Scenario bound to a specified AssemblyModel from a parsed mapping; strict validation remains separate.",
    "lock_joint": "Lock a specified joint in a Scenario, optionally at a position; this changes the verification condition.",
    "disable_constraint": "Disable a constraint by stable ID in a Scenario; use only for explicit diagnostic or comparison conditions.",
    "check_assembly_integrity": "Check that Components remain one connected assembly at every static or MotionResult sample and report disconnection, detachment, or escape.",
    "forward_component_poses": "Propagate world poses for all components from the assembly tree and joint positions.",
    "forward_connector_poses": "Propagate world poses for all connectors from the assembly tree and joint positions.",
    "find_singularities": "Compute Jacobian rank, minimum singular value, and condition number at actual MotionResult samples and report singular or near-singular samples.",
    "trace_connector_path": "Compute times, path length, endpoints, and world-coordinate bounds from a recorded connector trajectory.",
    "KinCheckError": "Public base class for all expected KinCheckAPI domain failures.",
    "MJCFAdapterError": "Raised when CADIR MJCF, mapping, or assets cannot be converted into AssemblyModel.",
    "AssemblyValidationError": "Raised when an assembly model or its references violate the structural contract.",
    "ScenarioValidationError": "Raised when Scenario time, state, drivers, or object references are invalid.",
    "BackendUnavailableError": "Raised when the requested calculation backend cannot be loaded.",
    "BackendCapabilityError": "Raised when the backend cannot express a capability explicitly requested by the caller.",
    "MotionSolveError": "Raised when motion solving starts but cannot produce a complete result; may include failure time and last valid result.",
    "GeometryCheckError": "Raised when interference, clearance, or motion-envelope operations fail.",
    "VerificationError": "Raised when a caller explicitly requires a structured check to pass and it fails.",
    "VisualizationExportError": "Raised when a viewer cannot be exported from public assembly and result data.",
    "MotionPackageError": "Raised when a `.kincheck` package cannot be written, read, or validated safely.",
}


SYMBOL_RULES: dict[str, tuple[str, ...]] = {
    "AdapterResult": (
        "Use `assembly` as the downstream verification input and retain `source_map` to trace CADIR source IDs.",
    ),
    "MotionResult": (
        "Only `completed` or a reviewed `completed_with_warnings` result may enter final acceptance; use `partial` only for diagnosis.",
        "Empty `sample_times_s` cannot establish any motion claim.",
    ),
    "ValidationResult": (
        "`passed` is derived from the absence of error issues; validation aggregates issues instead of failing fast.",
    ),
    "CheckReport": (
        "Read `passed` while preserving evidence, issues, metadata, checked objects, and thresholds.",
    ),
    "verify_transmission_ratio": (
        "This function emits `DeprecationWarning`; do not use it in new examples or implementations.",
    ),
    "check_envelope_interference": (
        "Both inputs must be `ClearanceReport` objects with `operation == 'motion_envelope'`.",
        "`metadata['confirmed_mesh_interference']` is always `False`; confirm overlap with an exact mesh check.",
    ),
    "set_component_result_scope": (
        "`requested` with an empty request list expands to all components as an explicit compatibility exception.",
    ),
    "list_executable_fixes": (
        "When no executable fix exists, this returns `()`; callers must not invent changes from that result.",
    ),
    "apply_assembly_fix": (
        "Currently always rejects execution with `KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED`.",
    ),
    "apply_scenario_fix": (
        "Currently always rejects execution with `KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED`.",
    ),
}


PARAMETER_NOTES: dict[str, str] = {
    "assembly": "The `AssemblyModel` to construct, validate, solve, or export.",
    "scenario": "An immutable `Scenario` bound to an assembly definition.",
    "motion_result": "The public `MotionResult` to query or check.",
    "xml_path": "Path to the CADIR-exported MJCF XML.",
    "mapping_path": "Path to the mapping JSON from the same export batch as the XML.",
    "asset_root": "Root directory within which meshes and other assets may resolve.",
    "path": "Input or output path as described by the operation.",
    "output_path": "Output file path.",
    "output_dir": "Output directory.",
    "time_s": "Query time in seconds within the result time range.",
    "start_time_s": "Start of the time window in seconds.",
    "end_time_s": "End of the time window in seconds.",
    "duration_s": "Total run duration in seconds; finite and positive.",
    "period_s": "Sampling period in seconds; finite and positive.",
    "joint_id": "Stable, resolvable joint ID.",
    "component_id": "Stable, resolvable component ID.",
    "connector_id": "Stable, resolvable connector ID.",
    "constraint_id": "Stable, resolvable constraint ID.",
    "check_id": "Stable caller-provided check ID for result traceability.",
    "parameters": "Explicit parameters for the check type; do not rely on unrecorded implicit acceptance defaults.",
    "options": "Public solve or analysis options; record the effective thresholds.",
    "status": "Structured status interpreted according to the stable values for the result type.",
    "passed": "Structured Boolean conclusion; read it together with issues and actual evidence.",
    "issues": "Structured issues preserving error codes, objects, and evidence.",
    "evidence": "Machine-readable evidence supporting the conclusion.",
    "metadata": "Additional read-only structured metadata.",
    "sample_times_s": "Strictly increasing actual sample times in seconds.",
    "joint_positions": "Joint positions keyed by stable ID; radians for rotation and metres for translation.",
    "target_component_id": "Component ID used as a geometric or kinematic target.",
    "target_connector_id": "Optional target connector ID; omission targets the component frame.",
    "expected_ratio": "Positive expected transmission-ratio magnitude; direction is separate.",
    "expected_direction": "Expected output direction relative to input: `same` or `opposite`.",
}


def clean_default(value: Any) -> str:
    if value is inspect.Signature.empty or value is dataclasses.MISSING:
        return "required"
    if isinstance(value, types.MappingProxyType):
        return "{}"
    text = repr(value)
    if text == "<factory>":
        return "default_factory"
    return f"`{text}`"


def purpose(name: str, value: Any, kind: str) -> str:
    if name in PURPOSE_OVERRIDES:
        return PURPOSE_OVERRIDES[name]
    doc = inspect.getdoc(value)
    if doc:
        return " ".join(doc.split())
    if kind == "function":
        verbs = {
            "add_": "Add data and return the updated immutable object",
            "set_": "Set a field and return the updated immutable object",
            "read_": "Read and reconstruct a public object",
            "write_": "Write a public object deterministically",
            "validate_": "Aggregate validation of the input contract",
            "check_": "Execute a structured check",
            "create_": "Create a public object",
            "list_": "Filter and return recorded structured evidence",
            "analyze_": "Analyze a kinematic property of a mechanism or result",
            "compute_": "Compute a backend-independent kinematic quantity",
            "solve_": "Solve the specified kinematic problem",
            "request_": "Request recording of an object in the result",
            "export_": "Export a public result asset",
            "format_": "Format a structured object",
        }
        for prefix, description in verbs.items():
            if name.startswith(prefix):
                return f"{description}: `{name}`."
        return f"Execute the public operation `{name}`."
    if kind == "enum":
        return f"Define the stable enum values accepted by `{name}`."
    if kind == "alias":
        return f"Define the public type contract used by `{name}`."
    if kind == "constant":
        return f"Expose the public constant `{name}`."
    return f"Represent the public, serializable `{name}` data structure."


def parameter_rows(value: Any, kind: str) -> list[tuple[str, str, str, str]]:
    if kind not in {"function", "class"}:
        return []
    try:
        signature = inspect.signature(value, eval_str=True)
    except (NameError, TypeError, ValueError):
        try:
            signature = inspect.signature(value)
        except (TypeError, ValueError):
            return []
    rows = []
    for name, parameter in signature.parameters.items():
        if name in {"self", "cls"}:
            continue
        note = PARAMETER_NOTES.get(name)
        if note is None:
            if name.endswith("_id"):
                note = f"Stable, resolvable `{name}`."
            elif name.endswith("_ids"):
                note = f"Explicitly specified `{name}` collection."
            elif name.endswith("_m_s2"):
                note = f"`{name}` in m/s^2; finite."
            elif name.endswith("_m_s"):
                note = f"`{name}` in m/s; finite."
            elif name.endswith("_rad_s"):
                note = f"`{name}` in rad/s; finite."
            elif name.endswith("_rad"):
                note = f"`{name}` in radians; finite."
            elif name.endswith("_m"):
                note = f"`{name}` in metres; finite."
            elif name.endswith("_s"):
                note = f"`{name}` in seconds; finite."
            else:
                note = f"Public input or data field `{name}`."
        rows.append(
            (
                name,
                source.clean_annotation(parameter.annotation),
                clean_default(parameter.default),
                note,
            )
        )
    return rows


def returns_text(value: Any, kind: str) -> str:
    if kind == "function":
        try:
            annotation = inspect.signature(value).return_annotation
        except (TypeError, ValueError):
            annotation = inspect.Signature.empty
        return f"Returns `{source.clean_annotation(annotation)}`."
    if kind == "class":
        if issubclass(value, Exception):
            return "Constructs a public domain exception. After catching it, read `code`, `report`, and structured context instead of matching free text."
        return "Constructs and returns an immutable public data object; field types and ranges are validated during construction."
    if kind == "enum":
        return "Use enum members or their stable string values; do not invent undefined states."
    if kind == "alias":
        return "This is a type contract, not a callable function."
    return "This is a read-only public constant, not a callable function."


def enum_section(value: type[enum.Enum]) -> list[str]:
    lines = ["## Enum Values", "", "| Member | Value |", "| --- | --- |"]
    lines.extend(f"| `{item.name}` | `{item.value}` |" for item in value)
    return lines


def page(module_name: str, import_module: str, name: str, value: Any) -> str:
    kind = source.effective_kind(name, value)
    lines = [
        f"# `{name}`",
        "",
        "## API Definition",
        "",
        "```python",
        source.signature_text(name, value, kind),
        "```",
        "",
        f"Source: `src/kincheckapi/{source.source_name(value, module_name)}`.",
        "",
        "## Import",
        "",
        "```python",
        f"from kincheckapi.{import_module} import {name}",
        "```",
        "",
        "## Purpose",
        "",
        purpose(name, value, kind),
        "",
    ]
    rows = parameter_rows(value, kind)
    if rows:
        lines.extend(
            [
                "## Parameters and Fields",
                "",
                "| Name | Type | Default | Description |",
                "| --- | --- | --- | --- |",
            ]
        )
        lines.extend(
            f"| `{field_name}` | `{annotation}` | {default} | {note} |"
            for field_name, annotation, default, note in rows
        )
        lines.append("")
    if kind == "enum":
        lines.extend(enum_section(value))
        lines.append("")
    lines.extend(["## Returns and Failures", "", returns_text(value, kind), ""])
    if module_name in {"checks", "clearance", "kinematics", "diagnostics"}:
        lines.extend(
            [
                "Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.",
                "",
            ]
        )
    lines.extend(["## Module Constraints", ""])
    lines.extend(f"- {rule}" for rule in MODULE_RULES[module_name])
    lines.extend(f"- {rule}" for rule in SYMBOL_RULES.get(name, ()))
    lines.extend(
        [
            "",
            "## Related Documentation",
            "",
            f"- [`{MODULES[module_name]['title']}`](README.md)",
            "- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)",
            "",
        ]
    )
    return "\n".join(lines)


def readme(module_name: str, exports: list[tuple[str, Any]]) -> str:
    info = MODULES[module_name]
    lines = [f"# {info['title']}", "", info["summary"], "", "## Public API", ""]
    if not exports:
        lines.extend(
            ["This release exposes no public operations; do not invent calls for this namespace.", ""]
        )
    else:
        lines.extend(["| Symbol | Type | Purpose |", "| --- | --- | --- |"])
    labels = {
        "function": "Function",
        "class": "Type",
        "enum": "Enum",
        "alias": "Type alias",
        "constant": "Constant",
    }
    for name, value in exports:
        kind = source.effective_kind(name, value)
        summary = purpose(name, value, kind).replace("\n", " ")
        lines.append(f"| [`{name}`]({name}.md) | {labels[kind]} | {summary} |")
    lines.extend(["", "## Module Rules", ""])
    lines.extend(f"- {rule}" for rule in MODULE_RULES[module_name])
    lines.append("")
    return "\n".join(lines)


def expected_files(repo: Path) -> dict[Path, str]:
    doc_root = repo / "skill" / "doc"
    expected: dict[Path, str] = {}
    for module_name in source.MODULES:
        module = importlib.import_module(f"kincheckapi.{module_name}")
        directory_name = source.MODULES[module_name].get("directory", module_name)
        directory = doc_root / directory_name
        exports = [
            (name, getattr(module, name))
            for name in source.public_names(module_name, module)
        ]
        expected[directory / "README.md"] = readme(module_name, exports)
        import_module = "trajectory_checks" if module_name == "trajectory_checks" else directory_name
        for name, value in exports:
            expected[directory / f"{name}.md"] = page(
                module_name, import_module, name, value
            )
    return expected


def generate(repo: Path, *, check: bool) -> int:
    expected = expected_files(repo)
    if check:
        failures = [
            path.relative_to(repo)
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        for directory in {path.parent for path in expected}:
            expected_here = {path for path in expected if path.parent == directory}
            failures.extend(
                path.relative_to(repo)
                for path in directory.glob("*.md")
                if path not in expected_here
            )
        if failures:
            print("English API docs are stale or missing:")
            for path in failures:
                print(f"- {path}")
            return 1
        print(f"English API docs are current: {len(expected)} files")
        return 0

    for directory in {path.parent for path in expected}:
        directory.mkdir(parents=True, exist_ok=True)
        for old in directory.glob("*.md"):
            old.unlink()
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print(f"Generated {len(expected)} English API documentation files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated docs differ")
    args = parser.parse_args()
    return generate(REPO_ROOT, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
