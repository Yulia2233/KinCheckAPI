# `InverseDynamicsResult`

## API Definition

```python
@dataclass(frozen=True)
class InverseDynamicsResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    request: kincheckapi.dynamic_types.DynamicRequest | None
    generalized_efforts: Mapping[str, float]
    generalized_units: Mapping[str, str]
    joint_powers_w: Mapping[str, float]
    body_wrenches: Mapping[str, Mapping[str, Any]]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import InverseDynamicsResult
```

## Purpose

Required generalized efforts and power at a prescribed state.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_inverse_dynamics'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `request` | `kincheckapi.dynamic_types.DynamicRequest | None` | `None` | Public input or data field `request`. |
| `generalized_efforts` | `Mapping[str, float]` | default_factory | Public input or data field `generalized_efforts`. |
| `generalized_units` | `Mapping[str, str]` | default_factory | Public input or data field `generalized_units`. |
| `joint_powers_w` | `Mapping[str, float]` | default_factory | Public input or data field `joint_powers_w`. |
| `body_wrenches` | `Mapping[str, Mapping[str, Any]]` | default_factory | Public input or data field `body_wrenches`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
