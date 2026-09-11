# `Limit`

## API Definition

```python
Limit = JointLimit
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Limit
```

## Purpose

JointLimit(lower: 'float', upper: 'float')

## Returns and Failures

This is a type contract, not a callable function.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
