# Pose Operations

Perform rigid-body pose operations using SI units and xyzw quaternion ordering.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`Pose`](Pose.md) | Type | Rigid transform expressed in SI units with an xyzw quaternion. |
| [`Quaternion`](Quaternion.md) | Type alias | Built-in immutable sequence. If no argument is given, the constructor returns an empty tuple. If iterable is specified the tuple is initialized from iterable's items. If the argument is a tuple, the return value is the same object. |
| [`Vector3`](Vector3.md) | Type alias | Built-in immutable sequence. If no argument is given, the constructor returns an empty tuple. If iterable is specified the tuple is initialized from iterable's items. If the argument is a tuple, the return value is the same object. |
| [`compose_pose`](compose_pose.md) | Function | Compose a parent pose with a child pose expressed in the parent frame. |
| [`inverse_pose`](inverse_pose.md) | Function | Return the inverse rigid transform. |
| [`orientation_error_rad`](orientation_error_rad.md) | Function | Compute the shortest unsigned angular error between two orientations in radians. |
| [`relative_pose`](relative_pose.md) | Function | Return the child pose relative to the parent frame. |
| [`rotate_vector`](rotate_vector.md) | Function | Rotate a vector using pose orientation without applying translation. |
| [`transform_point`](transform_point.md) | Function | Transform a local point into the parent frame through a pose. |

## Module Rules

- Use metres for positions and xyzw quaternion ordering.
- Input vectors and quaternions must be finite; zero-norm quaternions are invalid.
- State the reference frame for parent, child, actual, and expected values.
