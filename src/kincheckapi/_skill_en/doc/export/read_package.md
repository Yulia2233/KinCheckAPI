# `read_package`

## API Definition

```python
read_package(*, path: str | pathlib.Path) -> MotionPackage
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import read_package
```

## Purpose

Strictly validate and reconstruct a `.kincheck` package; raise `MotionPackageError` on failure.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | `str | pathlib.Path` | required | Input or output path as described by the operation. |

## Returns and Failures

Returns `MotionPackage`.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
