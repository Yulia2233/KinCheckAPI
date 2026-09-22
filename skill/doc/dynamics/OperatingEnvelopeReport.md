# `OperatingEnvelopeReport`

## API Definition

```python
@dataclass(frozen=True)
class OperatingEnvelopeReport:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    case_reports: Mapping[str, kincheckapi.fatigue.FatigueReport]
    worst_case_id: str | None
    worst_damage: float
    evaluated_count: int
    requested_count: int
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import OperatingEnvelopeReport
```

## Purpose

OperatingEnvelopeReport(*, operation: 'str' = 'evaluate_operating_envelope', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, case_reports: 'Mapping[str, FatigueReport]' = <factory>, worst_case_id: 'str | None' = None, worst_damage: 'float' = 0.0, evaluated_count: 'int' = 0, requested_count: 'int' = 0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'evaluate_operating_envelope'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `case_reports` | `Mapping[str, kincheckapi.fatigue.FatigueReport]` | default_factory | Public input or data field `case_reports`. |
| `worst_case_id` | `str | None` | `None` | Stable, resolvable `worst_case_id`. |
| `worst_damage` | `float` | `0.0` | Public input or data field `worst_damage`. |
| `evaluated_count` | `int` | `0` | Public input or data field `evaluated_count`. |
| `requested_count` | `int` | `0` | Public input or data field `requested_count`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
