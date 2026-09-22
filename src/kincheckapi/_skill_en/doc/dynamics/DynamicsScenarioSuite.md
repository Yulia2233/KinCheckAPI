# `DynamicsScenarioSuite`

## API Definition

```python
@dataclass(frozen=True)
class DynamicsScenarioSuite:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    matrix_id: str
    case_results: tuple[kincheckapi.dynamics_v07.MultibodyResult, ...]
    requested_case_ids: tuple[str, ...]
    evaluated_case_ids: tuple[str, ...]
    missing_case_ids: tuple[str, ...]
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import DynamicsScenarioSuite
```

## Purpose

DynamicsScenarioSuite(*, operation: 'str' = 'run_dynamics_cases', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, matrix_id: 'str' = '', case_results: 'tuple[MultibodyResult, ...]' = (), requested_case_ids: 'tuple[str, ...]' = (), evaluated_case_ids: 'tuple[str, ...]' = (), missing_case_ids: 'tuple[str, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'run_dynamics_cases'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `matrix_id` | `str` | `''` | Stable, resolvable `matrix_id`. |
| `case_results` | `tuple[kincheckapi.dynamics_v07.MultibodyResult, ...]` | `()` | Public input or data field `case_results`. |
| `requested_case_ids` | `tuple[str, ...]` | `()` | Explicitly specified `requested_case_ids` collection. |
| `evaluated_case_ids` | `tuple[str, ...]` | `()` | Explicitly specified `evaluated_case_ids` collection. |
| `missing_case_ids` | `tuple[str, ...]` | `()` | Explicitly specified `missing_case_ids` collection. |

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
