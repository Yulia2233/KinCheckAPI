# `ContactReport`

## API Definition

```python
@dataclass(frozen=True)
class ContactReport:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    contact_id: str
    normal_force_n: float
    tangential_force_n: float
    friction_limit_n: float
    pressure_pa: float | None
    utilization: Mapping[str, float]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import ContactReport
```

## Purpose

ContactReport(*, operation: 'str' = 'check_contact_capacity', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, contact_id: 'str' = '', normal_force_n: 'float' = 0.0, tangential_force_n: 'float' = 0.0, friction_limit_n: 'float' = 0.0, pressure_pa: 'float | None' = None, utilization: 'Mapping[str, float]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'check_contact_capacity'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `contact_id` | `str` | `''` | Stable, resolvable `contact_id`. |
| `normal_force_n` | `float` | `0.0` | Public input or data field `normal_force_n`. |
| `tangential_force_n` | `float` | `0.0` | Public input or data field `tangential_force_n`. |
| `friction_limit_n` | `float` | `0.0` | Public input or data field `friction_limit_n`. |
| `pressure_pa` | `float | None` | `None` | Public input or data field `pressure_pa`. |
| `utilization` | `Mapping[str, float]` | default_factory | Public input or data field `utilization`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
