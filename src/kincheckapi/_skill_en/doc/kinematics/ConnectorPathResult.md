# `ConnectorPathResult`

## API Definition

```python
@dataclass(frozen=True)
class ConnectorPathResult:
    component_id: str
    connector_id: str
    times_s: tuple[float, ...]
    positions_m: tuple[tuple[float, float, float], ...]
    path_length_m: float
    bounds_m: Mapping[str, tuple[float, float]]
    start_position_m: tuple[float, float, float] | None
    end_position_m: tuple[float, float, float] | None
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import ConnectorPathResult
```

## Purpose

Path statistics read from one recorded Connector trajectory.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `connector_id` | `str` | required | Stable, resolvable connector ID. |
| `times_s` | `tuple[float, ...]` | required | `times_s` in seconds; finite. |
| `positions_m` | `tuple[tuple[float, float, float], ...]` | required | `positions_m` in metres; finite. |
| `path_length_m` | `float` | required | `path_length_m` in metres; finite. |
| `bounds_m` | `Mapping[str, tuple[float, float]]` | required | `bounds_m` in metres; finite. |
| `start_position_m` | `tuple[float, float, float] | None` | required | `start_position_m` in metres; finite. |
| `end_position_m` | `tuple[float, float, float] | None` | required | `end_position_m` in metres; finite. |
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
