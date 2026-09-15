# `IntegrationSample`

## API Definition

```python
@dataclass(frozen=True)
class IntegrationSample:
    time_s: float
    component_poses: Mapping[str, Pose]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import IntegrationSample
```

## Purpose

Typed snapshot captured at an internal solver integration step.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `component_poses` | `Mapping[str, Pose]` | required | Public input or data field `component_poses`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
