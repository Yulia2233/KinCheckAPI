# `DofReport`

## API Definition

```python
@dataclass(frozen=True)
class DofReport:
    total_dofs: int
    joint_dofs: Mapping[str, int]
    component_dofs: Mapping[str, int]
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import DofReport
```

## Purpose

DofReport(*, total_dofs: 'int', joint_dofs: 'Mapping[str, int]', component_dofs: 'Mapping[str, int]', issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `total_dofs` | `int` | required | Public input or data field `total_dofs`. |
| `joint_dofs` | `Mapping[str, int]` | required | Public input or data field `joint_dofs`. |
| `component_dofs` | `Mapping[str, int]` | required | Public input or data field `component_dofs`. |
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
