# `solve_inverse_kinematics`

## API Definition

```python
solve_inverse_kinematics(*, assembly: AssemblyModel, target: Union[PoseTarget, Mapping[str, Any]], initial_joint_positions: Optional[Mapping[str, float]] = None, joint_limits: Optional[Mapping[str, Sequence[float]]] = None, solution_selection: Literal['first', 'lowest_residual', 'closest_to_initial'] = 'first', options: Union[kincheckapi.kinematics_ik.IKOptions, Mapping[str, Any], NoneType] = None) -> kincheckapi.kinematics_ik.IKSolutionSet
```

Source: `src/kincheckapi/kinematics_ik.py`.

## Import

```python
from kincheckapi.kinematics import solve_inverse_kinematics
```

## Purpose

Find verified scalar-joint configurations for one world-frame Pose target. Multistart is deterministic and finite, not exhaustive. Unsupported trajectory drivers and joint/constraint types return capability_failed with evidence. Invalid input and numerical failures are structured results, not empty passes.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `target` | `Union[PoseTarget, Mapping[str, Any]]` | required | Public input or data field `target`. |
| `initial_joint_positions` | `Optional[Mapping[str, float]]` | `None` | Public input or data field `initial_joint_positions`. |
| `joint_limits` | `Optional[Mapping[str, Sequence[float]]]` | `None` | Public input or data field `joint_limits`. |
| `solution_selection` | `Literal['first', 'lowest_residual', 'closest_to_initial']` | `'first'` | Public input or data field `solution_selection`. |
| `options` | `Union[kincheckapi.kinematics_ik.IKOptions, Mapping[str, Any], NoneType]` | `None` | Public solve or analysis options; record the effective thresholds. |

## Returns and Failures

Returns `IKSolutionSet`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
