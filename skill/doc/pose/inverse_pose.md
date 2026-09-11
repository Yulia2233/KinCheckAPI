# `inverse_pose`

## API Definition

```python
inverse_pose(*, pose: Pose) -> Pose
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.pose import inverse_pose
```

## Purpose

Return the inverse rigid transform.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `pose` | `Pose` | required | Public input or data field `pose`. |

## Returns and Failures

Returns `Pose`.

## Module Constraints

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.

## Related Documentation

- [`Pose Operations`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
