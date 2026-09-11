# `analyze_mobility`

## API Definition

```python
analyze_mobility(*, assembly: AssemblyModel, joint_positions: Optional[Mapping[str, float]] = None) -> MobilityReport
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics import analyze_mobility
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

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
