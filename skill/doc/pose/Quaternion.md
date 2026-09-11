# `Quaternion`

## API Definition

```python
Quaternion = tuple
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.pose import Quaternion
```

## Purpose

Built-in immutable sequence. If no argument is given, the constructor returns an empty tuple. If iterable is specified the tuple is initialized from iterable's items. If the argument is a tuple, the return value is the same object.

## Returns and Failures

This is a type contract, not a callable function.

## Module Constraints

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.

## Related Documentation

- [`Pose Operations`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
