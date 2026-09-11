# `relative_pose`

## API Definition

```python
relative_pose(*, parent: Pose, child: Pose) -> Pose
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.pose import relative_pose
```

## Purpose

Return the child pose relative to the parent frame.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `parent` | `Pose` | required | Public input or data field `parent`. |
| `child` | `Pose` | required | Public input or data field `child`. |

## Returns and Failures

Returns `Pose`.

## Module Constraints

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.

## Related Documentation

- [`Pose Operations`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
