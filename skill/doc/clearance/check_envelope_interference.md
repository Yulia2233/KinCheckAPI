# `check_envelope_interference`

## API Definition

```python
check_envelope_interference(*, first: ClearanceReport, second: ClearanceReport) -> ClearanceReport
```

Source: `src/kincheckapi/clearance.py`.

## Import

```python
from kincheckapi.clearance import check_envelope_interference
```

## Purpose

Compare world-axis-aligned bounds from two motion-envelope reports; this does not perform triangle-mesh interference or confirm penetration.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `first` | `ClearanceReport` | required | Public input or data field `first`. |
| `second` | `ClearanceReport` | required | Public input or data field `second`. |

## Returns and Failures

Returns `ClearanceReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Discrete interference, minimum-clearance, and envelope results use sampled states; call `check_continuous_interference()` explicitly for cross-sample evidence.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.
- Both inputs must be `ClearanceReport` objects with `operation == 'motion_envelope'`.
- `metadata['confirmed_mesh_interference']` is always `False`; confirm overlap with an exact mesh check.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
