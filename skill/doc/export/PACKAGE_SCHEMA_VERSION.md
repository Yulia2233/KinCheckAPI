# `PACKAGE_SCHEMA_VERSION`

## API Definition

```python
PACKAGE_SCHEMA_VERSION = 'kincheck.motion-package/1.0'
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import PACKAGE_SCHEMA_VERSION
```

## Purpose

Expose the public constant `PACKAGE_SCHEMA_VERSION`.

## Returns and Failures

This is a read-only public constant, not a callable function.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
