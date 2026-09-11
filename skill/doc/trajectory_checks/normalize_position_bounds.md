# `normalize_position_bounds`

## API Definition

```python
normalize_position_bounds(value: Optional[Mapping[str, Sequence[float]]]) -> Mapping[str, tuple[float, float]]
```

Source: `src/kincheckapi/trajectory_checks.py`.

## Import

```python
from kincheckapi.trajectory_checks import normalize_position_bounds
```

## Purpose

Normalize optional position bounds into a read-only per-axis `(lower, upper)` mapping and reject invalid bounds.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `value` | `Optional[Mapping[str, Sequence[float]]]` | required | Public input or data field `value`. |

## Returns and Failures

Returns `Mapping[str, tuple[float, float]]`.

## Module Constraints

- The time window must lie in the actual sample range and contain enough samples.
- Do not interpret empty windows or invalid position bounds as a pass.
- Path length and bounds are derived from discrete samples.

## Related Documentation

- [`Trajectory Utilities`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
