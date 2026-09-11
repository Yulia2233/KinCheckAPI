# `check_reachability`

## API Definition

```python
check_reachability(**kwargs: Any) -> ReachabilityResult
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import check_reachability
```

## Purpose

Check whether one requested Pose can be satisfied by the assembly.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `kwargs` | `Any` | required | Public input or data field `kwargs`. |

## Returns and Failures

Returns `ReachabilityResult`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
