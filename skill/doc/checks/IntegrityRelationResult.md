# `IntegrityRelationResult`

## API Definition

```python
@dataclass(frozen=True)
class IntegrityRelationResult:
    relation_id: str
    relation_type: Literal['mechanical', 'geometric', 'containment']
    component_a_id: str
    component_b_id: str
    time_s: float
    passed: bool
    measurement_m: float | None
    tolerance_m: float | None
    reason: str | None
```

Source: `src/kincheckapi/integrity.py`.

## Import

```python
from kincheckapi.checks import IntegrityRelationResult
```

## Purpose

One relation observation at one checked state.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `relation_id` | `str` | required | Stable, resolvable `relation_id`. |
| `relation_type` | `Literal['mechanical', 'geometric', 'containment']` | required | Public input or data field `relation_type`. |
| `component_a_id` | `str` | required | Stable, resolvable `component_a_id`. |
| `component_b_id` | `str` | required | Stable, resolvable `component_b_id`. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `measurement_m` | `float | None` | `None` | `measurement_m` in metres; finite. |
| `tolerance_m` | `float | None` | `None` | `tolerance_m` in metres; finite. |
| `reason` | `str | None` | `None` | Public input or data field `reason`. |

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
