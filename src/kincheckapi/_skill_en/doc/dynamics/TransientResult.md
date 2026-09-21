# `TransientResult`

## API Definition

```python
@dataclass(frozen=True)
class TransientResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    times_s: tuple[float, ...]
    displacement_m: tuple[tuple[float, ...], ...]
    velocity_m_s: tuple[tuple[float, ...], ...]
    acceleration_m_s2: tuple[tuple[float, ...], ...]
    time_step_s: float
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import TransientResult
```

## Purpose

TransientResult(*, operation: 'str' = 'solve_transient_response', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, times_s: 'tuple[float, ...]' = (), displacement_m: 'tuple[tuple[float, ...], ...]' = (), velocity_m_s: 'tuple[tuple[float, ...], ...]' = (), acceleration_m_s2: 'tuple[tuple[float, ...], ...]' = (), time_step_s: 'float' = 0.0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_transient_response'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `times_s` | `tuple[float, ...]` | `()` | `times_s` in seconds; finite. |
| `displacement_m` | `tuple[tuple[float, ...], ...]` | `()` | `displacement_m` in metres; finite. |
| `velocity_m_s` | `tuple[tuple[float, ...], ...]` | `()` | `velocity_m_s` in m/s; finite. |
| `acceleration_m_s2` | `tuple[tuple[float, ...], ...]` | `()` | `acceleration_m_s2` in m/s^2; finite. |
| `time_step_s` | `float` | `0.0` | `time_step_s` in seconds; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
