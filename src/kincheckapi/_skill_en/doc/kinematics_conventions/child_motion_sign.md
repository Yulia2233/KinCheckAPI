# `child_motion_sign`

## API Definition

```python
child_motion_sign(*, joint: Joint, child_group_id: str, component_groups: Mapping[str, str]) -> float
```

Source: `src/kincheckapi/kinematics_conventions.py`.

## Import

```python
from kincheckapi.kinematics_conventions import child_motion_sign
```

## Purpose

Convert the public joint coordinate into the motion sign of the current motion-tree child group.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint` | `Joint` | required | Public input or data field `joint`. |
| `child_group_id` | `str` | required | Stable, resolvable `child_group_id`. |
| `component_groups` | `Mapping[str, str]` | required | Public input or data field `component_groups`. |

## Returns and Failures

Returns `float`.

## Module Constraints

- Interpret the public joint scalar direction as `component_b - component_a`.
- Tree propagation may reverse authored connector order; use this module to convert the sign.
- Never infer sign from component names or tree traversal order.

## Related Documentation

- [`Kinematic Coordinate Conventions`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
