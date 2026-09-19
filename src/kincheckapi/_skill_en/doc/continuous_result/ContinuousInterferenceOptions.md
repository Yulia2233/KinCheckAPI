# `ContinuousInterferenceOptions`

## API Definition

```python
@dataclass(frozen=True)
class ContinuousInterferenceOptions:
    time_tolerance_s: float
    distance_tolerance_m: float
    minimum_clearance_m: float
    max_iterations: int
    max_subdivisions: int
    max_queries: int
    require_velocity_bound: bool
    interpolation: Optional[Literal['linear_pose', 'slerp_pose']]
    report_contact_normal: bool
```

Source: `src/kincheckapi/continuous_result.py`.

## Import

```python
from kincheckapi.continuous_result import ContinuousInterferenceOptions
```

## Purpose

Numerical budgets for a declared piecewise rigid motion model. slerp_pose means linear translation and exact shortest-arc SLERP per interval. linear_pose supports translation with constant orientation only. None means no between-sample model, so no continuous safety verdict is possible. max_iterations is the subdivision depth per input interval; max_subdivisions and max_queries are global budgets across every pair and input interval.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_tolerance_s` | `float` | `1e-05` | `time_tolerance_s` in seconds; finite. |
| `distance_tolerance_m` | `float` | `1e-06` | `distance_tolerance_m` in metres; finite. |
| `minimum_clearance_m` | `float` | `0.0` | `minimum_clearance_m` in metres; finite. |
| `max_iterations` | `int` | `64` | Public input or data field `max_iterations`. |
| `max_subdivisions` | `int` | `4096` | Public input or data field `max_subdivisions`. |
| `max_queries` | `int` | `100000` | Public input or data field `max_queries`. |
| `require_velocity_bound` | `bool` | `True` | Public input or data field `require_velocity_bound`. |
| `interpolation` | `Optional[Literal['linear_pose', 'slerp_pose']]` | `'slerp_pose'` | Public input or data field `interpolation`. |
| `report_contact_normal` | `bool` | `True` | Public input or data field `report_contact_normal`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- A continuous pass is conditional on the declared pose interpolation and piecewise velocity bound; it does not cover unrecorded deformable or dynamic motion.
- `failed` records contact or clearance violation; `indeterminate` means the budget, time axis, or geometric evidence cannot prove safety.
- Persist the event certainty, query/subdivision counts, options, and interval evidence with every report.

## Related Documentation

- [`Continuous Collision Evidence`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
