# `SamplingScope`

## API Definition

```python
SamplingScope = Literal
```

Source: `src/kincheckapi/clearance.py`.

## Import

```python
from kincheckapi.clearance import SamplingScope
```

## Purpose

Define the public type contract used by `SamplingScope`.

## Returns and Failures

This is a type contract, not a callable function.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Discrete interference, minimum-clearance, and envelope results use sampled states; call `check_continuous_interference()` explicitly for cross-sample evidence.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
