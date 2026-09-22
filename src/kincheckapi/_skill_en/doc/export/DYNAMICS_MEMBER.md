# `DYNAMICS_MEMBER`

## API Definition

```python
DYNAMICS_MEMBER = 'dynamics.json'
```

Source: `src/kincheckapi/export.py`.

## Import

```python
from kincheckapi.export import DYNAMICS_MEMBER
```

## Purpose

Expose the public constant `DYNAMICS_MEMBER`.

## Returns and Failures

This is a read-only public constant, not a callable function.

## Module Constraints

- Export only a completed and reviewed MotionResult; a result package is not a CADIR editing source.
- Validate member paths, schemas, hashes, and cross-file references before reading.
- With `require_meshes=True`, fail when any required mesh is missing.

## Related Documentation

- [`Result Packages`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
