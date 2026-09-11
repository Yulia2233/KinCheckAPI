# `orientation_error_rad`

## API Definition

```python
orientation_error_rad(*, actual: Pose, expected: Pose) -> float
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.pose import orientation_error_rad
```

## Purpose

Compute the shortest unsigned angular error between two orientations in radians.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `actual` | `Pose` | required | Public input or data field `actual`. |
| `expected` | `Pose` | required | Public input or data field `expected`. |

## Returns and Failures

Returns `float`.

## Module Constraints

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.

## Related Documentation

- [`Pose Operations`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
