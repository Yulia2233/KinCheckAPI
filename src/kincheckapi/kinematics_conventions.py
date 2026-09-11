"""Shared coordinate conventions for backend-neutral kinematics.

Public scalar Joint coordinates follow the authored Connector order:
``component_b - component_a``.  A kinematic tree may traverse that relation
in either direction, so tree propagation must convert the public value to the
child body's internal coordinate before applying a motion.
"""

from __future__ import annotations

from typing import Mapping

from .assembly import Joint


def child_motion_sign(
    *,
    joint: Joint,
    child_group_id: str,
    component_groups: Mapping[str, str],
) -> float:
    """Return the multiplier from a public Joint value to child motion.

    The result is ``+1`` when Connector B is on the child group and ``-1``
    when Connector A is on the child group.  This matches the public backend
    observable ``component_b - component_a`` for either tree direction.
    """

    group_a = component_groups.get(joint.connector_a.component_id)
    group_b = component_groups.get(joint.connector_b.component_id)
    if group_b == child_group_id and group_a != child_group_id:
        return 1.0
    if group_a == child_group_id and group_b != child_group_id:
        return -1.0
    raise ValueError(
        f"Joint {joint.joint_id!r} does not connect child group {child_group_id!r}"
    )


__all__ = ["child_motion_sign"]
