# `apply_assembly_fix`

## API Definition

```python
apply_assembly_fix(*, assembly: Any, fix: Fix) -> Any
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import apply_assembly_fix
```

## Purpose

Reserved automatic-fix entry point; v0.5.0 is unimplemented and raises `BackendCapabilityError`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `Any` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `fix` | `Fix` | required | Public input or data field `fix`. |

## Returns and Failures

Returns `Any`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.
- Currently always rejects execution with `KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED`.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
