# `run_dynamics_cases`

## API Definition

```python
run_dynamics_cases(*, matrix: kincheckapi.dynamics_v07.DynamicsScenarioMatrix) -> kincheckapi.dynamics_v07.DynamicsScenarioSuite
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import run_dynamics_cases
```

## Purpose

Solve every declared rigid-body case and report explicit coverage.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `matrix` | `kincheckapi.dynamics_v07.DynamicsScenarioMatrix` | required | Public input or data field `matrix`. |

## Returns and Failures

Returns `DynamicsScenarioSuite`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
