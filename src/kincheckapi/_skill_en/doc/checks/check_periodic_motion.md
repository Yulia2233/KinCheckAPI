# `check_periodic_motion`

## API Definition

```python
check_periodic_motion(*, motion_result: MotionResult, joint_id: str, period_s: float, periods: int = 1, position_tolerance: float = 1e-06, velocity_tolerance: float = 1e-06, check_id: str = 'periodic_motion') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_periodic_motion
```

## Purpose

Execute a structured check: `check_periodic_motion`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `period_s` | `float` | required | Sampling period in seconds; finite and positive. |
| `periods` | `int` | `1` | Public input or data field `periods`. |
| `position_tolerance` | `float` | `1e-06` | Public input or data field `position_tolerance`. |
| `velocity_tolerance` | `float` | `1e-06` | Public input or data field `velocity_tolerance`. |
| `check_id` | `str` | `'periodic_motion'` | Stable caller-provided check ID for result traceability. |

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
