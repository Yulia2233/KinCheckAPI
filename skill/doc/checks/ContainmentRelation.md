# `ContainmentRelation`

## API Definition

```python
@dataclass(frozen=True)
class ContainmentRelation:
    relation_id: str
    contained_component_id: str
    container_component_id: str
    axis: tuple[float, float, float]
    min_position_m: float
    max_position_m: float
    allowed_escape_tolerance_m: float
```

Source: `src/kincheckapi/integrity.py`.

## Import

```python
from kincheckapi.checks import ContainmentRelation
```

## Purpose

A declared relative-axis interval that keeps one component contained.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `relation_id` | `str` | required | Stable, resolvable `relation_id`. |
| `contained_component_id` | `str` | required | Stable, resolvable `contained_component_id`. |
| `container_component_id` | `str` | required | Stable, resolvable `container_component_id`. |
| `axis` | `tuple[float, float, float]` | `(0.0, 0.0, 1.0)` | Public input or data field `axis`. |
| `min_position_m` | `float` | `0.0` | `min_position_m` in metres; finite. |
| `max_position_m` | `float` | `0.0` | `max_position_m` in metres; finite. |
| `allowed_escape_tolerance_m` | `float` | `0.0001` | `allowed_escape_tolerance_m` in metres; finite. |

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
