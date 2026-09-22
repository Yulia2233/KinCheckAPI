# `ForwardDynamicsResult`

## API Definition

```python
@dataclass(frozen=True)
class ForwardDynamicsResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    request: kincheckapi.dynamic_types.ForwardDynamicsRequest | None
    samples: tuple[kincheckapi.dynamic_types.DynamicSample, ...]
    energy_input_j: float
    peak_power_w: float
    peak_effort: Mapping[str, float]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import ForwardDynamicsResult
```

## Purpose

ForwardDynamicsResult(*, operation: 'str' = 'solve_forward_dynamics', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, request: 'ForwardDynamicsRequest | None' = None, samples: 'tuple[DynamicSample, ...]' = (), energy_input_j: 'float' = 0.0, peak_power_w: 'float' = 0.0, peak_effort: 'Mapping[str, float]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_forward_dynamics'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `request` | `kincheckapi.dynamic_types.ForwardDynamicsRequest | None` | `None` | Public input or data field `request`. |
| `samples` | `tuple[kincheckapi.dynamic_types.DynamicSample, ...]` | `()` | Public input or data field `samples`. |
| `energy_input_j` | `float` | `0.0` | Public input or data field `energy_input_j`. |
| `peak_power_w` | `float` | `0.0` | Public input or data field `peak_power_w`. |
| `peak_effort` | `Mapping[str, float]` | default_factory | Public input or data field `peak_effort`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
