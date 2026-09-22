# `FrequencyResponseResult`

## API Definition

```python
@dataclass(frozen=True)
class FrequencyResponseResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    frequencies_hz: tuple[float, ...]
    response: tuple[tuple[complex, ...], ...]
    peak_amplitude: Mapping[str, float]
    damping: kincheckapi.vibration.DampingSpec | None
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import FrequencyResponseResult
```

## Purpose

FrequencyResponseResult(*, operation: 'str' = 'solve_frequency_response', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, frequencies_hz: 'tuple[float, ...]' = (), response: 'tuple[tuple[complex, ...], ...]' = (), peak_amplitude: 'Mapping[str, float]' = <factory>, damping: 'DampingSpec | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_frequency_response'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `frequencies_hz` | `tuple[float, ...]` | `()` | Public input or data field `frequencies_hz`. |
| `response` | `tuple[tuple[complex, ...], ...]` | `()` | Public input or data field `response`. |
| `peak_amplitude` | `Mapping[str, float]` | default_factory | Public input or data field `peak_amplitude`. |
| `damping` | `kincheckapi.vibration.DampingSpec | None` | `None` | Public input or data field `damping`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
