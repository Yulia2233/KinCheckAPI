# `ClearanceReport`

## API Definition

```python
@dataclass(frozen=True)
class ClearanceReport:
    operation: Literal['interference', 'minimum_clearance', 'motion_envelope']
    passed: bool
    status: Literal['passed', 'failed', 'capability_failed', 'partial']
    events: tuple[InterferenceEvent, ...]
    measurements: tuple[MinimumClearance, ...]
    envelopes: tuple[MotionEnvelope, ...]
    checked_component_pair_count: int
    checked_sample_count: int
    first_failure_time_s: float | None
    maximum_penetration_depth_m: float
    backend_id: str | None
    backend_version: str | None
    sampling_scope: Literal['motion_result', 'solver_steps']
    sampling_period_s: float
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/clearance_result.py`.

## Import

```python
from kincheckapi.clearance import ClearanceReport
```

## Purpose

ClearanceReport(*, operation: "Literal['interference', 'minimum_clearance', 'motion_envelope']", passed: 'bool', status: "Literal['passed', 'failed', 'capability_failed', 'partial']", events: 'tuple[InterferenceEvent, ...]' = (), measurements: 'tuple[MinimumClearance, ...]' = (), envelopes: 'tuple[MotionEnvelope, ...]' = (), checked_component_pair_count: 'int' = 0, checked_sample_count: 'int' = 0, first_failure_time_s: 'float | None' = None, maximum_penetration_depth_m: 'float' = 0.0, backend_id: 'str | None' = 'python-fcl', backend_version: 'str | None' = None, sampling_scope: 'SamplingScope' = 'motion_result', sampling_period_s: 'float' = 0.0, issues: 'tuple[SimIssue, ...]' = (), metadata: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `Literal['interference', 'minimum_clearance', 'motion_envelope']` | required | Public input or data field `operation`. |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `status` | `Literal['passed', 'failed', 'capability_failed', 'partial']` | required | Structured status interpreted according to the stable values for the result type. |
| `events` | `tuple[InterferenceEvent, ...]` | `()` | Public input or data field `events`. |
| `measurements` | `tuple[MinimumClearance, ...]` | `()` | Public input or data field `measurements`. |
| `envelopes` | `tuple[MotionEnvelope, ...]` | `()` | Public input or data field `envelopes`. |
| `checked_component_pair_count` | `int` | `0` | Public input or data field `checked_component_pair_count`. |
| `checked_sample_count` | `int` | `0` | Public input or data field `checked_sample_count`. |
| `first_failure_time_s` | `float | None` | `None` | `first_failure_time_s` in seconds; finite. |
| `maximum_penetration_depth_m` | `float` | `0.0` | `maximum_penetration_depth_m` in metres; finite. |
| `backend_id` | `str | None` | `'python-fcl'` | Stable, resolvable `backend_id`. |
| `backend_version` | `str | None` | `None` | Public input or data field `backend_version`. |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | Public input or data field `sampling_scope`. |
| `sampling_period_s` | `float` | `0.0` | `sampling_period_s` in seconds; finite. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Results come from triangle meshes and discrete time samples; they are not continuous-time collision proofs.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
