# `read_mjcf_mass_properties`

## API Definition

```python
read_mjcf_mass_properties(*, xml_path: str | pathlib.Path, mapping_path: str | pathlib.Path, ground_properties=None)
```

Source: `src/kincheckapi/physics_cadir.py`.

## Import

```python
from kincheckapi.dynamics import read_mjcf_mass_properties
```

## Purpose

Compatibility import of explicit MJCF inertials, labeled mjcf_explicit. Density-only meshes, shell assumptions and unspecified triangulation error have no strict acceptance path in v0.6.0. World mass must be supplied explicitly because MuJoCo worldbody does not retain physical ground mass.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `xml_path` | `str | pathlib.Path` | required | Path to the CADIR-exported MJCF XML. |
| `mapping_path` | `str | pathlib.Path` | required | Path to the mapping JSON from the same export batch as the XML. |
| `ground_properties` | `未标注` | `None` | Public input or data field `ground_properties`. |

## Returns and Failures

Returns `未标注`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
