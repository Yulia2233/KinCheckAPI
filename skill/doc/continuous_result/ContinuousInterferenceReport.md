# `ContinuousInterferenceReport`

## API Definition

```python
@dataclass(frozen=True)
class ContinuousInterferenceReport:
    status: Literal['passed', 'failed', 'indeterminate', 'capability_failed', 'validation_failed', 'partial']
    options: ContinuousInterferenceOptions | None
    events: tuple[ContinuousContactEvent, ...]
    checked_component_pair_count: int
    query_count: int
    subdivision_count: int
    minimum_clearance_m: float | None
    clearance_lower_bound_m: float | None
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/continuous_result.py`.

## Import

```python
from kincheckapi.continuous_result import ContinuousInterferenceReport
```

## Purpose

A conditional continuous verdict with certified and unresolved evidence. minimum_clearance_m is the minimum observed mesh-query distance, or None if bounding spheres suffice without mesh queries. clearance_lower_bound_m is a whole-scope bound and is None unless every interval is certified safe. Local safe bounds remain in metadata.certified_intervals. A confirmed collision keeps status failed even when later coverage or TOI refinement exhausts its budget; options, events and query counts are retained.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `status` | `Literal['passed', 'failed', 'indeterminate', 'capability_failed', 'validation_failed', 'partial']` | required | Structured status interpreted according to the stable values for the result type. |
| `options` | `ContinuousInterferenceOptions | None` | `None` | Public solve or analysis options; record the effective thresholds. |
| `events` | `tuple[ContinuousContactEvent, ...]` | `()` | Public input or data field `events`. |
| `checked_component_pair_count` | `int` | `0` | Public input or data field `checked_component_pair_count`. |
| `query_count` | `int` | `0` | Public input or data field `query_count`. |
| `subdivision_count` | `int` | `0` | Public input or data field `subdivision_count`. |
| `minimum_clearance_m` | `float | None` | `None` | `minimum_clearance_m` in metres; finite. |
| `clearance_lower_bound_m` | `float | None` | `None` | `clearance_lower_bound_m` in metres; finite. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- A continuous pass is conditional on the declared pose interpolation and piecewise velocity bound; it does not cover unrecorded deformable or dynamic motion.
- `failed` records contact or clearance violation; `indeterminate` means the budget, time axis, or geometric evidence cannot prove safety.
- Persist the event certainty, query/subdivision counts, options, and interval evidence with every report.

## Related Documentation

- [`Continuous Collision Evidence`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
