# `MotionResult`

## API Definition

```python
@dataclass(frozen=True)
class MotionResult:
    scenario_id: str
    assembly_id: str
    status: Literal['completed', 'completed_with_warnings', 'partial']
    start_time_s: float
    end_time_s: float
    sample_times_s: tuple[float, ...]
    joint_trajectories: Union[tuple[JointTrajectory, ...], Mapping[str, JointTrajectory]]
    trajectories: tuple[Trajectory, ...]
    constraint_residuals: tuple[ConstraintResidual, ...]
    constraint_equation_residuals: tuple[ConstraintEquationResidual, ...]
    closure_residuals: tuple[ConstraintResidual, ...]
    closure_statuses: Mapping[str, str]
    limit_events: tuple[LimitEvent, ...]
    issues: tuple[SimIssue, ...]
    backend_id: str | None
    backend_version: str | None
    metadata: Mapping[str, Any]
    integration_samples: tuple[IntegrationSample, ...]
    driver_trajectories: tuple[DriverTrajectory, ...]
    traceback: str | None
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import MotionResult
```

## Purpose

Stable output of any KinCheckAPI motion backend.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario_id` | `str` | required | Stable, resolvable `scenario_id`. |
| `assembly_id` | `str` | required | Stable, resolvable `assembly_id`. |
| `status` | `Literal['completed', 'completed_with_warnings', 'partial']` | required | Structured status interpreted according to the stable values for the result type. |
| `start_time_s` | `float` | required | Start of the time window in seconds. |
| `end_time_s` | `float` | required | End of the time window in seconds. |
| `sample_times_s` | `tuple[float, ...]` | required | Strictly increasing actual sample times in seconds. |
| `joint_trajectories` | `Union[tuple[JointTrajectory, ...], Mapping[str, JointTrajectory]]` | `()` | Public input or data field `joint_trajectories`. |
| `trajectories` | `tuple[Trajectory, ...]` | `()` | Public input or data field `trajectories`. |
| `constraint_residuals` | `tuple[ConstraintResidual, ...]` | `()` | Public input or data field `constraint_residuals`. |
| `constraint_equation_residuals` | `tuple[ConstraintEquationResidual, ...]` | `()` | Public input or data field `constraint_equation_residuals`. |
| `closure_residuals` | `tuple[ConstraintResidual, ...]` | `()` | Public input or data field `closure_residuals`. |
| `closure_statuses` | `Mapping[str, str]` | default_factory | Public input or data field `closure_statuses`. |
| `limit_events` | `tuple[LimitEvent, ...]` | `()` | Public input or data field `limit_events`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `backend_id` | `str | None` | `None` | Stable, resolvable `backend_id`. |
| `backend_version` | `str | None` | `None` | Public input or data field `backend_version`. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |
| `integration_samples` | `tuple[IntegrationSample, ...]` | `()` | Public input or data field `integration_samples`. |
| `driver_trajectories` | `tuple[DriverTrajectory, ...]` | `()` | Public input or data field `driver_trajectories`. |
| `traceback` | `str | None` | `None` | Public input or data field `traceback`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.
- Only `completed` or a reviewed `completed_with_warnings` result may enter final acceptance; use `partial` only for diagnosis.
- Empty `sample_times_s` cannot establish any motion claim.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
