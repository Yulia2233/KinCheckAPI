# `ContactDynamicsResult`

## API Definition

```python
@dataclass(frozen=True)
class ContactDynamicsResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    contact_id: str
    events: tuple[kincheckapi.dynamics_v07.ContactEvent, ...]
    impulse_ns: float
    momentum_residual_n_s: float
    energy_dissipation_j: float
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ContactDynamicsResult
```

## Purpose

ContactDynamicsResult(*, operation: 'str' = 'solve_contact_dynamics', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, contact_id: 'str' = '', events: 'tuple[ContactEvent, ...]' = (), impulse_ns: 'float' = 0.0, momentum_residual_n_s: 'float' = 0.0, energy_dissipation_j: 'float' = 0.0)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_contact_dynamics'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `contact_id` | `str` | `''` | Stable, resolvable `contact_id`. |
| `events` | `tuple[kincheckapi.dynamics_v07.ContactEvent, ...]` | `()` | Public input or data field `events`. |
| `impulse_ns` | `float` | `0.0` | Public input or data field `impulse_ns`. |
| `momentum_residual_n_s` | `float` | `0.0` | `momentum_residual_n_s` in seconds; finite. |
| `energy_dissipation_j` | `float` | `0.0` | Public input or data field `energy_dissipation_j`. |

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
