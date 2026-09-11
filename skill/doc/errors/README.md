# Public Exceptions

Define the stable KinCheckAPI exception hierarchy that callers can catch, serialize, and report.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`KinCheckError`](KinCheckError.md) | Type | Public base class for all expected KinCheckAPI domain failures. |
| [`MJCFAdapterError`](MJCFAdapterError.md) | Type | Raised when CADIR MJCF, mapping, or assets cannot be converted into AssemblyModel. |
| [`AssemblyValidationError`](AssemblyValidationError.md) | Type | Raised when an assembly model or its references violate the structural contract. |
| [`ScenarioValidationError`](ScenarioValidationError.md) | Type | Raised when Scenario time, state, drivers, or object references are invalid. |
| [`BackendUnavailableError`](BackendUnavailableError.md) | Type | Raised when the requested calculation backend cannot be loaded. |
| [`BackendCapabilityError`](BackendCapabilityError.md) | Type | Raised when the backend cannot express a capability explicitly requested by the caller. |
| [`MotionSolveError`](MotionSolveError.md) | Type | Raised when motion solving starts but cannot produce a complete result; may include failure time and last valid result. |
| [`GeometryCheckError`](GeometryCheckError.md) | Type | Raised when interference, clearance, or motion-envelope operations fail. |
| [`VerificationError`](VerificationError.md) | Type | Raised when a caller explicitly requires a structured check to pass and it fails. |
| [`VisualizationExportError`](VisualizationExportError.md) | Type | Raised when a viewer cannot be exported from public assembly and result data. |
| [`MotionPackageError`](MotionPackageError.md) | Type | Raised when a `.kincheck` package cannot be written, read, or validated safely. |

## Module Rules

- Catch `KinCheckError` for expected domain failures, then narrow to subclasses when needed.
- Preserve `code`, `report`, `object_ids`, `source_paths`, and `suggested_actions`.
- Do not choose repair behavior by matching exception message text.
