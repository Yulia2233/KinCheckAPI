# `check_joint_limits`

## API Definition

```python
check_joint_limits(*, assembly: AssemblyModel, motion_result: MotionResult, joint_ids: Optional[Sequence[str]] = None, tolerance: float = 0.0, start_time_s: float | None = None, end_time_s: float | None = None, check_id: str = 'joint_limits') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_joint_limits
```

## Purpose

Verify sampled joint positions against authored assembly limits.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `joint_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `joint_ids` collection. |
| `tolerance` | `float` | `0.0` | Public input or data field `tolerance`. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `check_id` | `str` | `'joint_limits'` | Stable caller-provided check ID for result traceability. |

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
