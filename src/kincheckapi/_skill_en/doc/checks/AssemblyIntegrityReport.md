# `AssemblyIntegrityReport`

## API Definition

```python
@dataclass(frozen=True)
class AssemblyIntegrityReport:
    passed: bool
    status: Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']
    checked_component_ids: tuple[str, ...]
    connected_component_ids: tuple[str, ...]
    disconnected_component_ids: tuple[str, ...]
    detached_component_ids: tuple[str, ...]
    out_of_bounds_component_ids: tuple[str, ...]
    failed_relation_ids: tuple[str, ...]
    failed_sample_times_s: tuple[float, ...]
    connected_network_count_by_sample: tuple[tuple[float, int], ...]
    geometric_connections: tuple[IntegrityRelationResult, ...]
    containment_results: tuple[IntegrityRelationResult, ...]
    mechanical_relation_results: tuple[IntegrityRelationResult, ...]
    checked_sample_count: int
    geometric_connection_tolerance_m: float
    penetration_tolerance_m: float
    containment_escape_tolerance_m: float
    sampling_scope: Literal['initial', 'motion_result']
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
    operation: str
```

Source: `src/kincheckapi/integrity.py`.

## Import

```python
from kincheckapi.checks import AssemblyIntegrityReport
```

## Purpose

Structured result for whole-assembly connectivity over checked states.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `status` | `Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']` | required | Structured status interpreted according to the stable values for the result type. |
| `checked_component_ids` | `tuple[str, ...]` | required | Explicitly specified `checked_component_ids` collection. |
| `connected_component_ids` | `tuple[str, ...]` | `()` | Explicitly specified `connected_component_ids` collection. |
| `disconnected_component_ids` | `tuple[str, ...]` | `()` | Explicitly specified `disconnected_component_ids` collection. |
| `detached_component_ids` | `tuple[str, ...]` | `()` | Explicitly specified `detached_component_ids` collection. |
| `out_of_bounds_component_ids` | `tuple[str, ...]` | `()` | Explicitly specified `out_of_bounds_component_ids` collection. |
| `failed_relation_ids` | `tuple[str, ...]` | `()` | Explicitly specified `failed_relation_ids` collection. |
| `failed_sample_times_s` | `tuple[float, ...]` | `()` | `failed_sample_times_s` in seconds; finite. |
| `connected_network_count_by_sample` | `tuple[tuple[float, int], ...]` | `()` | Public input or data field `connected_network_count_by_sample`. |
| `geometric_connections` | `tuple[IntegrityRelationResult, ...]` | `()` | Public input or data field `geometric_connections`. |
| `containment_results` | `tuple[IntegrityRelationResult, ...]` | `()` | Public input or data field `containment_results`. |
| `mechanical_relation_results` | `tuple[IntegrityRelationResult, ...]` | `()` | Public input or data field `mechanical_relation_results`. |
| `checked_sample_count` | `int` | `0` | Public input or data field `checked_sample_count`. |
| `geometric_connection_tolerance_m` | `float` | `0.0` | `geometric_connection_tolerance_m` in metres; finite. |
| `penetration_tolerance_m` | `float` | `0.0` | `penetration_tolerance_m` in metres; finite. |
| `containment_escape_tolerance_m` | `float` | `0.0` | `containment_escape_tolerance_m` in metres; finite. |
| `sampling_scope` | `Literal['initial', 'motion_result']` | `'initial'` | Public input or data field `sampling_scope`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |
| `operation` | `str` | `'check_assembly_integrity'` | Public input or data field `operation`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Each check must identify its objects, time window, expected value, threshold, and units.
- A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.
- Read `CheckReport.passed` together with evidence, issues, and metadata.
- Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.
- Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.

## Related Documentation

- [`Acceptance Checks`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
