# `GeneralizedJointState`

## API Definition

```python
@dataclass(frozen=True)
class GeneralizedJointState:
    joint_id: str
    position: tuple[float, ...] | float
    velocity: tuple[float, ...] | float
    acceleration: tuple[float, ...] | float
    coordinate_frame: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import GeneralizedJointState
```

## Purpose

A typed multi-DOF state for one rigid joint.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `position` | `tuple[float, ...] | float` | required | Public input or data field `position`. |
| `velocity` | `tuple[float, ...] | float` | `()` | Public input or data field `velocity`. |
| `acceleration` | `tuple[float, ...] | float` | `()` | Public input or data field `acceleration`. |
| `coordinate_frame` | `str` | `'joint'` | Public input or data field `coordinate_frame`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
