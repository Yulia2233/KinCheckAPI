# `StaticResult`

## API Definition

```python
@dataclass(frozen=True)
class StaticResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    request: kincheckapi.physics_types.StaticRequest | None
    generalized_holding: Mapping[str, float]
    generalized_units: Mapping[str, str]
    support_wrench: Mapping[str, Any]
    joint_reactions: Mapping[str, Any]
    body_residuals: Mapping[str, Any]
    component_poses: Mapping[str, Pose]
    load_wrenches: tuple[Mapping[str, Any], ...]
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import StaticResult
```

## Purpose

StaticResult(*, operation: 'str' = 'solve_static_equilibrium', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, request: 'StaticRequest | None' = None, generalized_holding: 'Mapping[str, float]' = <factory>, generalized_units: 'Mapping[str, str]' = <factory>, support_wrench: 'Mapping[str, Any]' = <factory>, joint_reactions: 'Mapping[str, Any]' = <factory>, body_residuals: 'Mapping[str, Any]' = <factory>, component_poses: 'Mapping[str, Pose]' = <factory>, load_wrenches: 'tuple[Mapping[str, Any], ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_static_equilibrium'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `request` | `kincheckapi.physics_types.StaticRequest | None` | `None` | Public input or data field `request`. |
| `generalized_holding` | `Mapping[str, float]` | default_factory | Public input or data field `generalized_holding`. |
| `generalized_units` | `Mapping[str, str]` | default_factory | Public input or data field `generalized_units`. |
| `support_wrench` | `Mapping[str, Any]` | default_factory | Public input or data field `support_wrench`. |
| `joint_reactions` | `Mapping[str, Any]` | default_factory | Public input or data field `joint_reactions`. |
| `body_residuals` | `Mapping[str, Any]` | default_factory | Public input or data field `body_residuals`. |
| `component_poses` | `Mapping[str, Pose]` | default_factory | Public input or data field `component_poses`. |
| `load_wrenches` | `tuple[Mapping[str, Any], ...]` | `()` | Public input or data field `load_wrenches`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
