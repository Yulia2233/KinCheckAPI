# Joint-Limit Events

Determine the first reached or exceeded event from assembly limits and joint trajectories.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`detect_limit_events`](detect_limit_events.md) | Function | Find the first reached or exceeded event for each modeled joint-limit side from actual trajectories. |

## Module Rules

- Event detection consumes actual joint trajectories and limits authored in the assembly.
- Missing limits or trajectories produce no events and do not establish a limit-check pass.
- Tolerance must be finite and non-negative.
