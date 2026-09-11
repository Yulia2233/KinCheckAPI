# `check_motion_envelope`

## API Definition

```python
check_motion_envelope(*, assembly: AssemblyModel, motion_result: MotionResult, check_id: str = 'motion_envelope', **parameters: Any) -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_motion_envelope
```

## Purpose

Compute a mesh motion envelope and expose it through the check API.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `check_id` | `str` | `'motion_envelope'` | Stable caller-provided check ID for result traceability. |
| `parameters` | `Any` | required | Explicit parameters for the check type; do not rely on unrecorded implicit acceptance defaults. |

## Returns and Failures

Returns `CheckReport`.

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
