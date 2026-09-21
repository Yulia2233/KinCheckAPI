# `ModalResult`

## API Definition

```python
@dataclass(frozen=True)
class ModalResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    frequencies_hz: tuple[float, ...]
    mode_shapes: tuple[tuple[float, ...], ...]
    effective_modal_mass: tuple[float, ...]
    normalization_mass: tuple[float, ...]
    omitted_frequency_hz: float | None
    normalized: str
```

Source: `src/kincheckapi/vibration.py`.

## Import

```python
from kincheckapi.dynamics import ModalResult
```

## Purpose

ModalResult(*, operation: 'str' = 'solve_modes', status: 'str' = 'passed', issues: 'tuple[SimIssue, ...]' = (), evidence: 'Mapping[str, Any]' = <factory>, model_sha256: 'str | None' = None, result_index: 'int | None' = None, frequencies_hz: 'tuple[float, ...]' = (), mode_shapes: 'tuple[tuple[float, ...], ...]' = (), effective_modal_mass: 'tuple[float, ...]' = (), normalization_mass: 'tuple[float, ...]' = (), omitted_frequency_hz: 'float | None' = None, normalized: 'str' = 'mass')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_modes'` | Public input or data field `operation`. |
| `status` | `str` | `'passed'` | Structured status interpreted according to the stable values for the result type. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `evidence` | `Mapping[str, Any]` | default_factory | Machine-readable evidence supporting the conclusion. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `result_index` | `int | None` | `None` | Public input or data field `result_index`. |
| `frequencies_hz` | `tuple[float, ...]` | `()` | Public input or data field `frequencies_hz`. |
| `mode_shapes` | `tuple[tuple[float, ...], ...]` | `()` | Public input or data field `mode_shapes`. |
| `effective_modal_mass` | `tuple[float, ...]` | `()` | Public input or data field `effective_modal_mass`. |
| `normalization_mass` | `tuple[float, ...]` | `()` | Public input or data field `normalization_mass`. |
| `omitted_frequency_hz` | `float | None` | `None` | Public input or data field `omitted_frequency_hz`. |
| `normalized` | `str` | `'mass'` | Public input or data field `normalized`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
