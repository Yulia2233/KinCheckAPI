# `solve_inverse_kinematics`

## API Definition

```python
solve_inverse_kinematics(*, assembly: AssemblyModel, target: Any, initial_joint_positions: Optional[Mapping[str, float]] = None, joint_limits: Optional[Mapping[str, Sequence[float]]] = None, solution_selection: str = 'first') -> Any
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import solve_inverse_kinematics
```

## Purpose

Explicit capability boundary for the not-yet-implemented general IK solver.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `target` | `Any` | required | Public input or data field `target`. |
| `initial_joint_positions` | `Optional[Mapping[str, float]]` | `None` | Public input or data field `initial_joint_positions`. |
| `joint_limits` | `Optional[Mapping[str, Sequence[float]]]` | `None` | Public input or data field `joint_limits`. |
| `solution_selection` | `str` | `'first'` | Public input or data field `solution_selection`. |

## Returns and Failures

Returns `Any`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
