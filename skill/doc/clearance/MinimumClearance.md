# `MinimumClearance`

## API Definition

```python
@dataclass(frozen=True)
class MinimumClearance:
    component_a_id: str
    component_b_id: str
    minimum_clearance_m: float
    time_s: float
    closest_point_a_m: tuple[float, float, float] | None
    closest_point_b_m: tuple[float, float, float] | None
    backend_id: str
    sampling_scope: Literal['motion_result', 'solver_steps']
```

Source: `src/kincheckapi/clearance_result.py`.

## Import

```python
from kincheckapi.clearance import MinimumClearance
```

## Purpose

MinimumClearance(*, component_a_id: 'str', component_b_id: 'str', minimum_clearance_m: 'float', time_s: 'float', closest_point_a_m: 'tuple[float, float, float] | None' = None, closest_point_b_m: 'tuple[float, float, float] | None' = None, backend_id: 'str' = 'python-fcl', sampling_scope: 'SamplingScope' = 'motion_result')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_a_id` | `str` | required | Stable, resolvable `component_a_id`. |
| `component_b_id` | `str` | required | Stable, resolvable `component_b_id`. |
| `minimum_clearance_m` | `float` | required | `minimum_clearance_m` in metres; finite. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `closest_point_a_m` | `tuple[float, float, float] | None` | `None` | `closest_point_a_m` in metres; finite. |
| `closest_point_b_m` | `tuple[float, float, float] | None` | `None` | `closest_point_b_m` in metres; finite. |
| `backend_id` | `str` | `'python-fcl'` | Stable, resolvable `backend_id`. |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | Public input or data field `sampling_scope`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Results come from triangle meshes and discrete time samples; they are not continuous-time collision proofs.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
