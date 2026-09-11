# `CheckReport`

## API Definition

```python
@dataclass(frozen=True)
class CheckReport:
    check_id: str
    check_type: str
    passed: bool
    severity: Literal['info', 'warning', 'error']
    evidence: tuple[Evidence, ...]
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import CheckReport
```

## Purpose

One deterministic, machine-readable verification outcome.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `check_id` | `str` | required | Stable caller-provided check ID for result traceability. |
| `check_type` | `str` | required | Public input or data field `check_type`. |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `severity` | `Literal['info', 'warning', 'error']` | required | Public input or data field `severity`. |
| `evidence` | `tuple[Evidence, ...]` | `()` | Machine-readable evidence supporting the conclusion. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Each check must identify its objects, time window, expected value, threshold, and units.
- A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.
- Read `CheckReport.passed` together with evidence, issues, and metadata.
- Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.
- Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.
- Read `passed` while preserving evidence, issues, metadata, checked objects, and thresholds.

## Related Documentation

- [`Acceptance Checks`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
