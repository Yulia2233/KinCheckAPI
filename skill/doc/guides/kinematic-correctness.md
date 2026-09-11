# Kinematic Correctness

In KinCheckAPI, “correct” means that the model satisfies checkable kinematic facts under the specified condition, not merely that the solver returned without raising.

## Required Layers

1. **Model**: component, connector, joint, ground, closure, and coupling references exist; IDs are unique; units and poses are sensible.
2. **Topology**: the motion tree is connected, ground is explicit, closure count matches the design, and DOFs and drivers are not obviously contradictory.
3. **Pose**: the initial joint position produces valid poses and closure position/orientation residuals stay within thresholds.
4. **Motion**: the requested driver completes the full time window with sufficient samples, no unintended limit violation, and the expected transmission relationship.
5. **Task**: target component/connector poses, trajectories, reachability, or workspace satisfy the user's requirement.
6. **Safety**: when requested, explicit component pairs pass interference and minimum-clearance checks.

Report the failed layer and its evidence; do not hide an earlier failure with a later result.

## Common Misreadings

- `status == "partial"` is not “mostly passed”; it is valid evidence before an incomplete solve.
- `checked_sample_count == 0` is not “no interference”; it means no valid check was executed.
- A DOF report alone does not prove mechanism motion; verify target motion and constraint residuals too.
- A joint `range` is the modeled limit. Missing limits may produce “not modeled”, not an automatic pass.
- Kinematic and geometric interference verification are separate dimensions and cannot replace one another.
