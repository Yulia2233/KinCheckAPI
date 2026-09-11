# `transform_point`

## API Definition

```python
transform_point(*, pose: Pose, point_m: Sequence[float]) -> tuple[float, float, float]
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.pose import transform_point
```

## Purpose

Transform a local point into the parent frame through a pose.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `pose` | `Pose` | required | Public input or data field `pose`. |
| `point_m` | `Sequence[float]` | required | `point_m` in metres; finite. |

## Returns and Failures

Returns `Vector3`.

## Module Constraints

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.

## Related Documentation

- [`Pose Operations`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
