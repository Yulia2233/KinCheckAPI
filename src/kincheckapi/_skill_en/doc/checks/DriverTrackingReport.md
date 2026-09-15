# `DriverTrackingReport`

## API Definition

```python
@dataclass(frozen=True)
class DriverTrackingReport:
    passed: bool
    joint_id: str
    mode: str
    maximum_absolute_error: float
    mean_absolute_error: float
    rms_error: float
    overshoot: float
    undertracking: float
    settling_time_s: float | None
    valid_sample_count: int
    first_failure_time_s: float | None
    tolerance: float
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import DriverTrackingReport
```

## Purpose

Acceptance evidence comparing declared driver targets with actual samples.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `mode` | `str` | required | Public input or data field `mode`. |
| `maximum_absolute_error` | `float` | required | Public input or data field `maximum_absolute_error`. |
| `mean_absolute_error` | `float` | required | Public input or data field `mean_absolute_error`. |
| `rms_error` | `float` | required | Public input or data field `rms_error`. |
| `overshoot` | `float` | required | Public input or data field `overshoot`. |
| `undertracking` | `float` | `0.0` | Public input or data field `undertracking`. |
| `settling_time_s` | `float | None` | required | `settling_time_s` in seconds; finite. |
| `valid_sample_count` | `int` | required | Public input or data field `valid_sample_count`. |
| `first_failure_time_s` | `float | None` | required | `first_failure_time_s` in seconds; finite. |
| `tolerance` | `float` | required | Public input or data field `tolerance`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |

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
