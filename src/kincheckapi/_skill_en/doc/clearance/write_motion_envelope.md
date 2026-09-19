# `write_motion_envelope`

## API Definition

```python
write_motion_envelope(*, report: ClearanceReport, path: str | pathlib.Path) -> None
```

Source: `src/kincheckapi/clearance.py`.

## Import

```python
from kincheckapi.clearance import write_motion_envelope
```

## Purpose

Write a public object deterministically: `write_motion_envelope`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `report` | `ClearanceReport` | required | Public input or data field `report`. |
| `path` | `str | pathlib.Path` | required | Input or output path as described by the operation. |

## Returns and Failures

Returns `None`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Discrete interference, minimum-clearance, and envelope results use sampled states; call `check_continuous_interference()` explicitly for cross-sample evidence.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
