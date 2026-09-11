# Kinematic Coordinate Conventions

Define stable sign conventions between authored connector order and motion-tree propagation direction.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`child_motion_sign`](child_motion_sign.md) | Function | Convert the public joint coordinate into the motion sign of the current motion-tree child group. |

## Module Rules

- Interpret the public joint scalar direction as `component_b - component_a`.
- Tree propagation may reverse authored connector order; use this module to convert the sign.
- Never infer sign from component names or tree traversal order.
