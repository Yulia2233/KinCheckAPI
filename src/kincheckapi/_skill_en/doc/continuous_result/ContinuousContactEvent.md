# `ContinuousContactEvent`

## API Definition

```python
@dataclass(frozen=True)
class ContinuousContactEvent:
    component_a_id: str
    component_b_id: str
    time_interval_s: tuple[float, float]
    earliest_contact_time_s: float | None
    state_time_s: float
    signed_distance_m: float | None
    confirmed: bool
    certainty: Literal['certified', 'bracketed', 'indeterminate']
    event_type: Literal['contact', 'clearance_violation', 'initial_overlap', 'possible_contact']
    position_a_m: tuple[float, float, float] | None
    position_b_m: tuple[float, float, float] | None
    contact_normal: tuple[float, float, float] | None
    normal_source: str
    relative_velocity_m_s: tuple[float, float, float] | None
    relative_speed_m_s: float | None
    closing_speed_m_s: float | None
    contact_angle_rad: float | None
    pre_contact_time_s: float | None
    pre_contact_relative_velocity_m_s: tuple[float, float, float] | None
    evidence: tuple[Evidence, ...]
```

Source: `src/kincheckapi/continuous_result.py`.

## Import

```python
from kincheckapi.continuous_result import ContinuousContactEvent
```

## Purpose

First possible entry and observed violation for one explicit component pair. earliest_contact_time_s is an upper bound, never an exact impact claim. time_interval_s retains the earliest unresolved prefix; toi_tolerance_met in evidence records whether the bracket meets the requested precision. Geometry and velocities refer to state_time_s. Positive signed distance is separation; non-positive FCL contact evidence is not an exact penetration metric. Relative velocity is world-space point velocity B - A, including rotation. pre_contact_time_s identifies an observed separated sample, not proof that the whole preceding motion is collision-free.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_a_id` | `str` | required | Stable, resolvable `component_a_id`. |
| `component_b_id` | `str` | required | Stable, resolvable `component_b_id`. |
| `time_interval_s` | `tuple[float, float]` | required | `time_interval_s` in seconds; finite. |
| `earliest_contact_time_s` | `float | None` | required | `earliest_contact_time_s` in seconds; finite. |
| `state_time_s` | `float` | required | `state_time_s` in seconds; finite. |
| `signed_distance_m` | `float | None` | required | `signed_distance_m` in metres; finite. |
| `confirmed` | `bool` | required | Public input or data field `confirmed`. |
| `certainty` | `Literal['certified', 'bracketed', 'indeterminate']` | required | Public input or data field `certainty`. |
| `event_type` | `Literal['contact', 'clearance_violation', 'initial_overlap', 'possible_contact']` | required | Public input or data field `event_type`. |
| `position_a_m` | `tuple[float, float, float] | None` | `None` | `position_a_m` in metres; finite. |
| `position_b_m` | `tuple[float, float, float] | None` | `None` | `position_b_m` in metres; finite. |
| `contact_normal` | `tuple[float, float, float] | None` | `None` | Public input or data field `contact_normal`. |
| `normal_source` | `str` | `'unavailable'` | Public input or data field `normal_source`. |
| `relative_velocity_m_s` | `tuple[float, float, float] | None` | `None` | `relative_velocity_m_s` in m/s; finite. |
| `relative_speed_m_s` | `float | None` | `None` | `relative_speed_m_s` in m/s; finite. |
| `closing_speed_m_s` | `float | None` | `None` | `closing_speed_m_s` in m/s; finite. |
| `contact_angle_rad` | `float | None` | `None` | `contact_angle_rad` in radians; finite. |
| `pre_contact_time_s` | `float | None` | `None` | `pre_contact_time_s` in seconds; finite. |
| `pre_contact_relative_velocity_m_s` | `tuple[float, float, float] | None` | `None` | `pre_contact_relative_velocity_m_s` in m/s; finite. |
| `evidence` | `tuple[Evidence, ...]` | `()` | Machine-readable evidence supporting the conclusion. |

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
