# `analyze_mobility`

## API Definition

```python
analyze_mobility(*, assembly: AssemblyModel, joint_positions: Optional[Mapping[str, float]] = None) -> MobilityReport
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import analyze_mobility
```

## Purpose

Analyze effective mechanism degrees of freedom from nominal joint DOFs and constraint Jacobian rank.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_positions` | `Optional[Mapping[str, float]]` | `None` | Joint positions keyed by stable ID; radians for rotation and metres for translation. |

## Returns and Failures

Returns `MobilityReport`.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
