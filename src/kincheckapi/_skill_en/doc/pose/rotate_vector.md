# `rotate_vector`

## API Definition

```python
rotate_vector(*, pose: Pose, vector: Sequence[float]) -> tuple[float, float, float]
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.pose import rotate_vector
```

## Purpose

Rotate a vector using pose orientation without applying translation.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `pose` | `Pose` | required | Public input or data field `pose`. |
| `vector` | `Sequence[float]` | required | Public input or data field `vector`. |

## Returns and Failures

Returns `Vector3`.

## Module Constraints

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.

## Related Documentation

- [`Pose Operations`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
