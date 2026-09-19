# `IKSolutionSet`

## API Definition

```python
@dataclass(frozen=True)
class IKSolutionSet:
    status: Literal['solved', 'unreachable', 'nonconverged', 'singular', 'invalid', 'capability_failed']
    target: PoseTarget | None
    options: kincheckapi.kinematics_ik.IKOptions | None
    solutions: tuple[kincheckapi.kinematics_ik.IKSolution, ...]
    selected_solution: kincheckapi.kinematics_ik.IKSolution | None
    attempts: tuple[kincheckapi.kinematics_ik.IKSolution, ...]
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/kinematics_ik.py`.

## Import

```python
from kincheckapi.kinematics import IKSolutionSet
```

## Purpose

Verified distinct solutions and all attempts; no claim of exhaustive search.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `status` | `Literal['solved', 'unreachable', 'nonconverged', 'singular', 'invalid', 'capability_failed']` | required | Structured status interpreted according to the stable values for the result type. |
| `target` | `PoseTarget | None` | `None` | Public input or data field `target`. |
| `options` | `kincheckapi.kinematics_ik.IKOptions | None` | `None` | Public solve or analysis options; record the effective thresholds. |
| `solutions` | `tuple[kincheckapi.kinematics_ik.IKSolution, ...]` | `()` | Public input or data field `solutions`. |
| `selected_solution` | `kincheckapi.kinematics_ik.IKSolution | None` | `None` | Public input or data field `selected_solution`. |
| `attempts` | `tuple[kincheckapi.kinematics_ik.IKSolution, ...]` | `()` | Public input or data field `attempts`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |

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
