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

str(object='') -> str str(bytes_or_buffer[, encoding[, errors]]) -> str Create a new string object from the given object. If encoding or errors is specified, then the object must expose a data buffer that will be decoded using the given encoding and error handler. Otherwise, returns the result of object.__str__() (if defined) or repr(object). encoding defaults to sys.getdefaultencoding(). errors defaults to 'strict'.

## Returns and Failures

This is a read-only public constant, not a callable function.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
