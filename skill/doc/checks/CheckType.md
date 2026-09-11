# `CheckType`

## API Definition

```python
CheckType = Literal
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import CheckType
```

## Purpose

Define the public type contract used by `CheckType`.

## Returns and Failures

This is a type contract, not a callable function.

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
