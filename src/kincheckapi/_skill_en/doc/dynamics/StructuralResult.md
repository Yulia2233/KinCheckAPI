# `StructuralResult`

## API Definition

```python
@dataclass(frozen=True)
class StructuralResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    displacements_m: Mapping[str, float]
    reactions_n: Mapping[str, float]
    stresses_pa: Mapping[str, float]
    strains: Mapping[str, float]
    load_resultant: tuple[float, ...]
    residual_norm: float
    converged: bool
    roi: tuple[str, ...]
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import StructuralResult
```

## Purpose

StructuralResult(*, operation: 'str' = 'solve_static_structure', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, displacements_m: 'Mapping[str, float]' = <factory>, reactions_n: 'Mapping[str, float]' = <factory>, stresses_pa: 'Mapping[str, float]' = <factory>, strains: 'Mapping[str, float]' = <factory>, load_resultant: 'tuple[float, ...]' = (), residual_norm: 'float' = 0.0, converged: 'bool' = False, roi: 'tuple[str, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_static_structure'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `displacements_m` | `Mapping[str, float]` | default_factory | `displacements_m` in metres; finite. |
| `reactions_n` | `Mapping[str, float]` | default_factory | Public input or data field `reactions_n`. |
| `stresses_pa` | `Mapping[str, float]` | default_factory | Public input or data field `stresses_pa`. |
| `strains` | `Mapping[str, float]` | default_factory | Public input or data field `strains`. |
| `load_resultant` | `tuple[float, ...]` | `()` | Public input or data field `load_resultant`. |
| `residual_norm` | `float` | `0.0` | Public input or data field `residual_norm`. |
| `converged` | `bool` | `False` | Public input or data field `converged`. |
| `roi` | `tuple[str, ...]` | `()` | Public input or data field `roi`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
