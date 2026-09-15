# `VIEWER_SCHEMA_VERSION`

## API Definition

```python
VIEWER_SCHEMA_VERSION = 'kincheck.viewer/1.0'
```

Source: `src/kincheckapi/visualization.py`.

## Import

```python
from kincheckapi.visualization import VIEWER_SCHEMA_VERSION
```

## Purpose

Expose the public constant `VIEWER_SCHEMA_VERSION`.

## Returns and Failures

This is a read-only public constant, not a callable function.

## Module Constraints

- Visualization consumes only public AssemblyModel and MotionResult data, not private backend state.
- Inspect motion status, recorded trajectories, and mesh assets before export.
- Use the viewer to review evidence, not as a replacement for numerical acceptance checks.

## Related Documentation

- [`Offline Visualization`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
