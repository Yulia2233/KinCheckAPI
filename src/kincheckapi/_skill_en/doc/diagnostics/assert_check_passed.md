# `assert_check_passed`

## API Definition

```python
assert_check_passed(*, check: Any) -> None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import assert_check_passed
```

## Purpose

Require a structured check to pass; otherwise raise `VerificationError` while preserving the original check.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `check` | `Any` | required | Public input or data field `check`. |

## Returns and Failures

Returns `None`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
