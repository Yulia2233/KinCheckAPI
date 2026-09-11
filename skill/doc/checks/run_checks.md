# `run_checks`

## API Definition

```python
run_checks(*, assembly: 'AssemblyModel', scenario: 'Scenario | None' = None, motion_result: 'MotionResult | None' = None, checks: 'Sequence[CheckSpec]') -> 'CheckSuiteReport'
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import run_checks
```

## Purpose

Execute explicit acceptance claims in `CheckSpec` order and return a `CheckSuiteReport`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `scenario` | `Scenario | None` | `None` | An immutable `Scenario` bound to an assembly definition. |
| `motion_result` | `MotionResult | None` | `None` | The public `MotionResult` to query or check. |
| `checks` | `Sequence[CheckSpec]` | required | Public input or data field `checks`. |

## Returns and Failures

Returns `CheckSuiteReport`.

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
