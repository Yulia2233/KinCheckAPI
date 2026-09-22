# `DynamicsLoadHistory`

## API Definition

```python
@dataclass(frozen=True)
class DynamicsLoadHistory:
    history_id: str
    model_sha256: str | None
    scenario_id: str
    times_s: tuple[float, ...]
    records: tuple[Mapping[str, Any], ...]
    schema_version: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import DynamicsLoadHistory
```

## Purpose

DynamicsLoadHistory(*, history_id: 'str', model_sha256: 'str | None', scenario_id: 'str', times_s: 'tuple[float, ...]', records: 'tuple[Mapping[str, Any], ...]', schema_version: 'str' = 'kincheck.dynamics-history/1.0', status: 'str' = 'completed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `history_id` | `str` | required | Stable, resolvable `history_id`. |
| `model_sha256` | `str | None` | required | Public input or data field `model_sha256`. |
| `scenario_id` | `str` | required | Stable, resolvable `scenario_id`. |
| `times_s` | `tuple[float, ...]` | required | `times_s` in seconds; finite. |
| `records` | `tuple[Mapping[str, Any], ...]` | required | Public input or data field `records`. |
| `schema_version` | `str` | `'kincheck.dynamics-history/1.0'` | Public input or data field `schema_version`. |
| `status` | `str` | `'completed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |

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
