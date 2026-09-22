# `PhysicsError`

## API Definition

```python
class PhysicsError(KinCheckError): ...

PhysicsError(*, code: 'str', message: 'str | None' = None, report: 'DiagnosticReport | ValidationResult | None' = None, object_ids: 'Sequence[str]' = (), source_paths: 'Sequence[str]' = (), suggested_actions: 'Sequence[str]' = (), details: 'Mapping[str, Any] | None' = None, operation: 'str | None' = None, status: 'str | None' = None, stage: 'str | None' = None) -> 'None'
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import PhysicsError
```

## Purpose

Invalid, unavailable, or conflicting physics input; never a placeholder.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `code` | `str` | required | Public input or data field `code`. |
| `message` | `str | None` | `None` | Public input or data field `message`. |
| `report` | `DiagnosticReport | ValidationResult | None` | `None` | Public input or data field `report`. |
| `object_ids` | `Sequence[str]` | `()` | Explicitly specified `object_ids` collection. |
| `source_paths` | `Sequence[str]` | `()` | Public input or data field `source_paths`. |
| `suggested_actions` | `Sequence[str]` | `()` | Public input or data field `suggested_actions`. |
| `details` | `Optional[Mapping[str, Any]]` | `None` | Public input or data field `details`. |
| `operation` | `str | None` | `None` | Public input or data field `operation`. |
| `status` | `str | None` | `None` | Structured status interpreted according to the stable values for the result type. |
| `stage` | `str | None` | `None` | Public input or data field `stage`. |

## Returns and Failures

Constructs a public domain exception. After catching it, read `code`, `report`, and structured context instead of matching free text.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
