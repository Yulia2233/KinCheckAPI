# `WorkspaceOptions`

## API Definition

```python
@dataclass(frozen=True)
class WorkspaceOptions:
    joint_ranges: Mapping[str, Sequence[float]]
    samples_per_joint: int
    max_samples: int
    seed: int | None
    position_tolerance_m: float
    orientation_tolerance_rad: float
    singularity_tolerance: float
    near_singularity_tolerance: float
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import WorkspaceOptions
```

## Purpose

Explicit finite ranges for deterministic workspace sampling.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_ranges` | `Mapping[str, Sequence[float]]` | default_factory | Public input or data field `joint_ranges`. |
| `samples_per_joint` | `int` | `9` | Public input or data field `samples_per_joint`. |
| `max_samples` | `int` | `4096` | Public input or data field `max_samples`. |
| `seed` | `int | None` | `None` | Public input or data field `seed`. |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad` in radians; finite. |
| `singularity_tolerance` | `float` | `1e-08` | Public input or data field `singularity_tolerance`. |
| `near_singularity_tolerance` | `float` | `0.0001` | Public input or data field `near_singularity_tolerance`. |

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
