# `validate_package`

## API Definition

```python
validate_package(*, path: str | pathlib.Path) -> ValidationResult
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import validate_package
```

## Purpose

Validate `.kincheck` member paths, schemas, hashes, and cross-file references and return an aggregate validation result.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | `str | pathlib.Path` | required | Input or output path as described by the operation. |

## Returns and Failures

Returns `ValidationResult`.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
