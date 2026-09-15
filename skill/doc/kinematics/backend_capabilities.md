# `backend_capabilities`

## API Definition

```python
backend_capabilities() -> KinematicCapabilities
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import backend_capabilities
```

## Purpose

Execute the public operation `backend_capabilities`.

## Returns and Failures

Returns `KinematicCapabilities`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
