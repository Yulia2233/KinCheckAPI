# `DriveDutySummary`

## API Definition

```python
@dataclass(frozen=True)
class DriveDutySummary:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    torque_peak_nm: float
    torque_rms_nm: float
    speed_peak_rad_s: float
    power_peak_w: float
    energy_positive_j: float
    energy_negative_j: float
    energy_net_j: float
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import DriveDutySummary
```

## Purpose

DriveDutySummary(*, operation: 'str' = 'summarize_drive_duty', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, torque_peak_nm: 'float' = 0.0, torque_rms_nm: 'float' = 0.0, speed_peak_rad_s: 'float' = 0.0, power_peak_w: 'float' = 0.0, energy_positive_j: 'float' = 0.0, energy_negative_j: 'float' = 0.0, energy_net_j: 'float' = 0.0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'summarize_drive_duty'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `torque_peak_nm` | `float` | `0.0` | Public input or data field `torque_peak_nm`. |
| `torque_rms_nm` | `float` | `0.0` | Public input or data field `torque_rms_nm`. |
| `speed_peak_rad_s` | `float` | `0.0` | `speed_peak_rad_s` in rad/s; finite. |
| `power_peak_w` | `float` | `0.0` | Public input or data field `power_peak_w`. |
| `energy_positive_j` | `float` | `0.0` | Public input or data field `energy_positive_j`. |
| `energy_negative_j` | `float` | `0.0` | Public input or data field `energy_negative_j`. |
| `energy_net_j` | `float` | `0.0` | Public input or data field `energy_net_j`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
