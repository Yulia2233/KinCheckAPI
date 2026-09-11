# `MobilityReport`

## API Definition

```python
@dataclass(frozen=True)
class MobilityReport:
    nominal_dofs: int
    effective_dofs: int
    joint_dofs: Mapping[str, int]
    constraint_rank: int
    constraint_ids: tuple[str, ...]
    singular_values: tuple[float, ...]
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import MobilityReport
```

## Purpose

MobilityReport(*, nominal_dofs: 'int', effective_dofs: 'int', joint_dofs: 'Mapping[str, int]', constraint_rank: 'int', constraint_ids: 'tuple[str, ...]' = (), singular_values: 'tuple[float, ...]' = (), issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `nominal_dofs` | `int` | required | Public input or data field `nominal_dofs`. |
| `effective_dofs` | `int` | required | Public input or data field `effective_dofs`. |
| `joint_dofs` | `Mapping[str, int]` | required | Public input or data field `joint_dofs`. |
| `constraint_rank` | `int` | required | Public input or data field `constraint_rank`. |
| `constraint_ids` | `tuple[str, ...]` | `()` | Explicitly specified `constraint_ids` collection. |
| `singular_values` | `tuple[float, ...]` | `()` | Public input or data field `singular_values`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
