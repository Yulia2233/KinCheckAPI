# Continuous Collision Evidence

Define conservative continuous-interference options, contact events, and auditable reports across trajectory intervals.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`ContinuousInterferenceOptions`](ContinuousInterferenceOptions.md) | Type | Numerical budgets for a declared piecewise rigid motion model. slerp_pose means linear translation and exact shortest-arc SLERP per interval. linear_pose supports translation with constant orientation only. None means no between-sample model, so no continuous safety verdict is possible. max_iterations is the subdivision depth per input interval; max_subdivisions and max_queries are global budgets across every pair and input interval. |
| [`ContinuousContactEvent`](ContinuousContactEvent.md) | Type | First possible entry and observed violation for one explicit component pair. earliest_contact_time_s is an upper bound, never an exact impact claim. time_interval_s retains the earliest unresolved prefix; toi_tolerance_met in evidence records whether the bracket meets the requested precision. Geometry and velocities refer to state_time_s. Positive signed distance is separation; non-positive FCL contact evidence is not an exact penetration metric. Relative velocity is world-space point velocity B - A, including rotation. pre_contact_time_s identifies an observed separated sample, not proof that the whole preceding motion is collision-free. |
| [`ContinuousInterferenceReport`](ContinuousInterferenceReport.md) | Type | A conditional continuous verdict with certified and unresolved evidence. minimum_clearance_m is the minimum observed mesh-query distance, or None if bounding spheres suffice without mesh queries. clearance_lower_bound_m is a whole-scope bound and is None unless every interval is certified safe. Local safe bounds remain in metadata.certified_intervals. A confirmed collision keeps status failed even when later coverage or TOI refinement exhausts its budget; options, events and query counts are retained. |

## Module Rules

- A continuous pass is conditional on the declared pose interpolation and piecewise velocity bound; it does not cover unrecorded deformable or dynamic motion.
- `failed` records contact or clearance violation; `indeterminate` means the budget, time axis, or geometric evidence cannot prove safety.
- Persist the event certainty, query/subdivision counts, options, and interval evidence with every report.
