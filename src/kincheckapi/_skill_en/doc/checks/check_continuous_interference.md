# `check_continuous_interference`

## API Definition

```python
check_continuous_interference(*, assembly: AssemblyModel, motion_result: MotionResult, component_pairs: Optional[Sequence[Sequence[str]]] = None, **parameters: Any) -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_continuous_interference
```

## Purpose

Check explicit component pairs between recorded trajectory samples.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_pairs` | `Optional[Sequence[Sequence[str]]]` | `None` | Public input or data field `component_pairs`. |
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
