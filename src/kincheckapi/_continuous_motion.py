"""Exact piecewise rigid interpolation and mesh distance queries used by CCD."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import math

import numpy as np

from . import _clearance_fcl as backend
from .pose import Pose, _multiply_quaternions, _conjugate_quaternion


def rotation_vector(first: Pose, second: Pose) -> np.ndarray:
    q = np.asarray(_multiply_quaternions(second.orientation_xyzw, _conjugate_quaternion(first.orientation_xyzw)))
    # Canonical tie-break at pi also makes q and -q describe identical motion.
    if q[3] < 0 or (q[3] == 0 and tuple(q[:3]) < (0, 0, 0)):
        q = -q
    norm = float(np.linalg.norm(q[:3]))
    return q[:3] * (2 * math.atan2(norm, q[3]) / norm) if norm else np.zeros(3)


@dataclass(frozen=True)
class RigidSegment:
    start: float
    end: float
    first: Pose
    second: Pose

    @property
    def velocity(self) -> np.ndarray:
        return (np.asarray(self.second.position_m) - np.asarray(self.first.position_m)) / (self.end - self.start)

    @property
    def omega(self) -> np.ndarray:
        return rotation_vector(self.first, self.second) / (self.end - self.start)

    def pose(self, time: float) -> Pose:
        if not self.start <= time <= self.end:
            raise ValueError("continuous pose query is outside its segment")
        f = (time - self.start) / (self.end - self.start)
        r = rotation_vector(self.first, self.second)
        angle = float(np.linalg.norm(r))
        dq = (*tuple(r * (math.sin(angle * f / 2) / angle)), math.cos(angle * f / 2)) if angle else (0., 0., 0., 1.)
        return Pose(position_m=tuple((1 - f) * a + f * b for a, b in zip(self.first.position_m, self.second.position_m)),
                    orientation_xyzw=_multiply_quaternions(dq, self.first.orientation_xyzw))

    def point_velocity(self, time: float, point: tuple[float, float, float]) -> np.ndarray:
        return self.velocity + np.cross(self.omega, np.asarray(point) - np.asarray(self.pose(time).position_m))


def segment_at(times: tuple[float, ...], poses: tuple[Pose, ...], time: float) -> RigidSegment:
    if not times[0] <= time <= times[-1]:
        raise ValueError("recorded trajectory does not cover the checked time")
    index = min(max(bisect_right(times, time) - 1, 0), len(times) - 2)
    return RigidSegment(times[index], times[index + 1], poses[index], poses[index + 1])


@dataclass(frozen=True)
class DistanceSample:
    time: float
    collided: bool
    distance: float
    point_a: tuple[float, float, float] | None
    point_b: tuple[float, float, float] | None
    normal: tuple[float, float, float] | None
    normal_source: str


class MeshPairQuery:
    """Keep two FCL objects alive for all the interval queries of this pair."""

    def __init__(self, mesh_a: backend.MeshModel, mesh_b: backend.MeshModel, report_normal: bool):
        self.a, self.b = mesh_a, mesh_b
        self.fcl, self.version = backend.require_backend()
        self.object_a = self.fcl.CollisionObject(mesh_a.model)
        self.object_b = self.fcl.CollisionObject(mesh_b.model)
        self.radius_a = max(math.hypot(*v) for v in mesh_a.vertices)
        self.radius_b = max(math.hypot(*v) for v in mesh_b.vertices)
        self.report_normal = report_normal

    def query(self, time: float, pose_a: Pose, pose_b: Pose) -> DistanceSample:
        self.object_a.setTransform(backend._transform(pose_a))
        self.object_b.setTransform(backend._transform(pose_b))
        result = self.fcl.CollisionResult()
        self.fcl.collide(self.object_a, self.object_b, self.fcl.CollisionRequest(num_max_contacts=100, enable_contact=True), result)
        if result.is_collision:
            contacts = tuple(result.contacts)
            contact = contacts[0] if contacts else None
            point = tuple(float(v) for v in contact.pos) if contact is not None else None
            depths = [float(c.penetration_depth) for c in contacts if math.isfinite(float(c.penetration_depth)) and c.penetration_depth > 0]
            normal = None
            if self.report_normal and contact is not None:
                raw = np.asarray(contact.normal, dtype=float)
                size = float(np.linalg.norm(raw))
                if np.all(np.isfinite(raw)) and size > 1e-12:
                    normal = tuple(float(v) for v in raw / size)
            return DistanceSample(time, True, -min(depths, default=0.), point, point, normal, "fcl_contact_a_to_b" if normal else "unavailable")
        result = self.fcl.DistanceResult()
        self.fcl.distance(self.object_a, self.object_b, self.fcl.DistanceRequest(enable_nearest_points=True, enable_signed_distance=False), result)
        distance = float(result.min_distance)
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("FCL returned an invalid separation distance")
        points = tuple(result.nearest_points) if result.nearest_points is not None else ()
        a = tuple(float(v) for v in points[0]) if len(points) == 2 else None
        b = tuple(float(v) for v in points[1]) if len(points) == 2 else None
        # Surface intersection tests alone miss complete containment.
        if math.dist(pose_a.position_m, pose_b.position_m) <= self.radius_a + self.radius_b:
            if backend._contains_any_closed_component(self.a, pose_a, self.b, pose_b) or backend._contains_any_closed_component(self.b, pose_b, self.a, pose_a):
                return DistanceSample(time, True, -distance, a, b, None, "unavailable_containment")
        normal = None
        if self.report_normal and a is not None and b is not None:
            delta = np.asarray(b) - np.asarray(a)
            size = float(np.linalg.norm(delta))
            if size > 1e-12 and np.all(np.isfinite(delta)):
                normal = tuple(float(v) for v in delta / size)
        return DistanceSample(time, False, distance, a, b, normal, "nearest_points_a_to_b" if normal else "unavailable")


def sphere_lower_bound(a: RigidSegment, b: RigidSegment, left: float, right: float, radii: float) -> float:
    start = np.asarray(b.pose(left).position_m) - np.asarray(a.pose(left).position_m)
    end = np.asarray(b.pose(right).position_m) - np.asarray(a.pose(right).position_m)
    delta = end - start
    den = float(delta @ delta)
    f = max(0., min(1., -float(start @ delta) / den)) if den else 0.
    return float(np.linalg.norm(start + f * delta)) - radii
