# `BucklingResult`

## API Definition

```python
@dataclass(frozen=True)
class BucklingResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    eigenvalues: tuple[float, ...]
    mode_shapes: tuple[tuple[float, ...], ...]
    reference_load_n: float
    converged: bool
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import BucklingResult
```

## Purpose

BucklingResult(*, operation: 'str' = 'solve_buckling_screening', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, eigenvalues: 'tuple[float, ...]' = (), mode_shapes: 'tuple[tuple[float, ...], ...]' = (), reference_load_n: 'float' = 0.0, converged: 'bool' = False)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_buckling_screening'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `eigenvalues` | `tuple[float, ...]` | `()` | Public input or data field `eigenvalues`. |
| `mode_shapes` | `tuple[tuple[float, ...], ...]` | `()` | Public input or data field `mode_shapes`. |
| `reference_load_n` | `float` | `0.0` | Public input or data field `reference_load_n`. |
| `converged` | `bool` | `False` | Public input or data field `converged`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
