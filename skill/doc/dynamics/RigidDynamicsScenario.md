# `RigidDynamicsScenario`

## API Definition

```python
@dataclass(frozen=True)
class RigidDynamicsScenario:
    states: tuple[kincheckapi.dynamics_v07.GeneralizedJointState, ...]
    mass_matrix: tuple[tuple[float, ...], ...]
    force_vector: tuple[float, ...]
    duration_s: float
    sample_period_s: float
    damping_matrix: tuple[tuple[float, ...], ...] | None
    stiffness_matrix: tuple[tuple[float, ...], ...] | None
    constraints: tuple[kincheckapi.dynamics_v07.ConstraintSpec, ...]
    model_sha256: str | None
    scenario_id: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import RigidDynamicsScenario
```

## Purpose

RigidDynamicsScenario(*, states: 'tuple[GeneralizedJointState, ...]', mass_matrix: 'tuple[tuple[float, ...], ...]', force_vector: 'tuple[float, ...]', duration_s: 'float', sample_period_s: 'float', damping_matrix: 'tuple[tuple[float, ...], ...] | None' = None, stiffness_matrix: 'tuple[tuple[float, ...], ...] | None' = None, constraints: 'tuple[ConstraintSpec, ...]' = (), model_sha256: 'str | None' = None, scenario_id: 'str' = '')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `states` | `tuple[kincheckapi.dynamics_v07.GeneralizedJointState, ...]` | required | Public input or data field `states`. |
| `mass_matrix` | `tuple[tuple[float, ...], ...]` | required | Public input or data field `mass_matrix`. |
| `force_vector` | `tuple[float, ...]` | required | Public input or data field `force_vector`. |
| `duration_s` | `float` | required | Total run duration in seconds; finite and positive. |
| `sample_period_s` | `float` | required | `sample_period_s` in seconds; finite. |
| `damping_matrix` | `tuple[tuple[float, ...], ...] | None` | `None` | Public input or data field `damping_matrix`. |
| `stiffness_matrix` | `tuple[tuple[float, ...], ...] | None` | `None` | Public input or data field `stiffness_matrix`. |
| `constraints` | `tuple[kincheckapi.dynamics_v07.ConstraintSpec, ...]` | `()` | Public input or data field `constraints`. |
| `model_sha256` | `str | None` | `None` | Public input or data field `model_sha256`. |
| `scenario_id` | `str` | `''` | Stable, resolvable `scenario_id`. |

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
