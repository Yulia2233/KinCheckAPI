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
from kincheckapi.kinematics import MobilityReport
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

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
