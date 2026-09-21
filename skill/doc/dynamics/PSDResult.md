# `PSDResult`

## API Definition

```python
@dataclass(frozen=True)
class PSDResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    frequency_hz: tuple[float, ...]
    psd: tuple[float, ...]
    unit: str
    variance: float
    sample_rate_hz: float
    segment_count: int
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import PSDResult
```

## Purpose

PSDResult(*, operation: 'str' = 'estimate_psd', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, frequency_hz: 'tuple[float, ...]' = (), psd: 'tuple[float, ...]' = (), unit: 'str' = '', variance: 'float' = 0.0, sample_rate_hz: 'float' = 0.0, segment_count: 'int' = 0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'estimate_psd'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `frequency_hz` | `tuple[float, ...]` | `()` | Public input or data field `frequency_hz`. |
| `psd` | `tuple[float, ...]` | `()` | Public input or data field `psd`. |
| `unit` | `str` | `''` | Public input or data field `unit`. |
| `variance` | `float` | `0.0` | Public input or data field `variance`. |
| `sample_rate_hz` | `float` | `0.0` | Public input or data field `sample_rate_hz`. |
| `segment_count` | `int` | `0` | Public input or data field `segment_count`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
