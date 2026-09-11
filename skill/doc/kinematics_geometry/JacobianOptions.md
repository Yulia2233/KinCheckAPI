# `JacobianOptions`

## API Definition

```python
@dataclass(frozen=True)
class JacobianOptions:
    finite_difference_step: float
    rank_tolerance: float
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import JacobianOptions
```

## Purpose

JacobianOptions(*, finite_difference_step: 'float' = 1e-07, rank_tolerance: 'float' = 1e-09)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `finite_difference_step` | `float` | `1e-07` | Public input or data field `finite_difference_step`. |
| `rank_tolerance` | `float` | `1e-09` | Public input or data field `rank_tolerance`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
