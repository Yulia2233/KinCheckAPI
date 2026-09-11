# `CheckSpec`

## API Definition

```python
@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    check_type: str
    parameters: Mapping[str, Any]
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import CheckSpec
```

## Purpose

Explicit instruction consumed by :func:`run_checks`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `check_id` | `str` | required | Stable caller-provided check ID for result traceability. |
| `check_type` | `str` | required | Public input or data field `check_type`. |
| `parameters` | `Mapping[str, Any]` | default_factory | Explicit parameters for the check type; do not rely on unrecorded implicit acceptance defaults. |

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
