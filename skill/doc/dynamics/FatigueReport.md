# `FatigueReport`

## API Definition

```python
@dataclass(frozen=True)
class FatigueReport:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    history_id: str
    material_id: str
    cycles: tuple[kincheckapi.fatigue.FatigueCycle, ...]
    damage: float
    allowable_damage: float
    life_repeats: float
    correction: str
    residual_indices: tuple[int, ...]
```

Source: `src/kincheckapi/fatigue.py`.

## Import

```python
from kincheckapi.dynamics import FatigueReport
```

## Purpose

FatigueReport(*, operation: 'str' = 'evaluate_fatigue', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, history_id: 'str' = '', material_id: 'str' = '', cycles: 'tuple[FatigueCycle, ...]' = (), damage: 'float' = 0.0, allowable_damage: 'float' = 1.0, life_repeats: 'float' = inf, correction: 'str' = 'none', residual_indices: 'tuple[int, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'evaluate_fatigue'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `history_id` | `str` | `''` | Stable, resolvable `history_id`. |
| `material_id` | `str` | `''` | Stable, resolvable `material_id`. |
| `cycles` | `tuple[kincheckapi.fatigue.FatigueCycle, ...]` | `()` | Public input or data field `cycles`. |
| `damage` | `float` | `0.0` | Public input or data field `damage`. |
| `allowable_damage` | `float` | `1.0` | Public input or data field `allowable_damage`. |
| `life_repeats` | `float` | `inf` | Public input or data field `life_repeats`. |
| `correction` | `str` | `'none'` | Public input or data field `correction`. |
| `residual_indices` | `tuple[int, ...]` | `()` | Public input or data field `residual_indices`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
