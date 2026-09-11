# `TransmissionRatioCheck`

## API Definition

```python
@dataclass(frozen=True)
class TransmissionRatioCheck:
    passed: bool
    expected_ratio: float
    measured_ratio: float | None
    relative_error: float | None
    expected_direction: Literal['same', 'opposite']
    measured_direction: Optional[Literal['same', 'opposite']]
    input_joint_id: str
    output_joint_id: str
    input_member: str | None
    output_member: str | None
    fixed_member: str | None
    sample_count: int
    rejected_sample_count: int
    start_time_s: float | None
    end_time_s: float | None
    stage_checks: tuple[_PlanetaryStageEvidence, ...]
    evidence: tuple[Evidence, ...]
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import TransmissionRatioCheck
```

## Purpose

TransmissionRatioCheck(*, passed: 'bool', expected_ratio: 'float', measured_ratio: 'float | None', relative_error: 'float | None', expected_direction: 'Direction', measured_direction: 'Direction | None', input_joint_id: 'str', output_joint_id: 'str', input_member: 'str | None' = None, output_member: 'str | None' = None, fixed_member: 'str | None' = None, sample_count: 'int' = 0, rejected_sample_count: 'int' = 0, start_time_s: 'float | None' = None, end_time_s: 'float | None' = None, stage_checks: 'tuple[_PlanetaryStageEvidence, ...]' = (), evidence: 'tuple[Evidence, ...]' = (), issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `expected_ratio` | `float` | required | Positive expected transmission-ratio magnitude; direction is separate. |
| `measured_ratio` | `float | None` | required | Public input or data field `measured_ratio`. |
| `relative_error` | `float | None` | required | Public input or data field `relative_error`. |
| `expected_direction` | `Literal['same', 'opposite']` | required | Expected output direction relative to input: `same` or `opposite`. |
| `measured_direction` | `Optional[Literal['same', 'opposite']]` | required | Public input or data field `measured_direction`. |
| `input_joint_id` | `str` | required | Stable, resolvable `input_joint_id`. |
| `output_joint_id` | `str` | required | Stable, resolvable `output_joint_id`. |
| `input_member` | `str | None` | `None` | Public input or data field `input_member`. |
| `output_member` | `str | None` | `None` | Public input or data field `output_member`. |
| `fixed_member` | `str | None` | `None` | Public input or data field `fixed_member`. |
| `sample_count` | `int` | `0` | Public input or data field `sample_count`. |
| `rejected_sample_count` | `int` | `0` | Public input or data field `rejected_sample_count`. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `stage_checks` | `tuple[_PlanetaryStageEvidence, ...]` | `()` | Public input or data field `stage_checks`. |
| `evidence` | `tuple[Evidence, ...]` | `()` | Machine-readable evidence supporting the conclusion. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
