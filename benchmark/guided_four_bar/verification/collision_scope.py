"""Expand exported rigid groups into all physical occurrences for collision review.

Only public KinCheckAPI models/APIs and Python's standard library are used.
Leaf STL files are exported from the same CAD build as scene.xml; no geometry
is invented or simplified here. The MJCF geom transform supplies each leaf's
rigid offset from its recorded parent group trajectory.
"""
from dataclasses import replace
from itertools import combinations
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from kincheckapi.assembly import AssemblyModel, Component, Part
from kincheckapi.pose import Pose, compose_pose
from kincheckapi.result import Trajectory


def physical_motion(model_dir: Path, assembly, motion):
    mapping = json.loads((model_dir / "scene.mapping.json").read_text())
    xml = ET.parse(model_dir / "scene.xml").getroot()
    world = xml.find("worldbody")
    mesh_definitions = {v: k for k, v in mapping["meshes"].items()}
    trajectories = {t.component_id: t for t in motion.trajectories if t.connector_id is None}
    parts, components, traces, group_for = {}, [], [], {}
    for group in mapping["groups"]:
        owner = world if group["body_name"] is None else world.find(f".//body[@name='{group['body_name']}']")
        if owner is None:
            raise ValueError(f"Missing physical group {group['group_id']}")
        for geom in owner.findall("geom"):
            definition = mesh_definitions[geom.attrib["mesh"]]
            component_id = f"node/{mapping['root_definition_id']}/{geom.attrib['name']}"
            if component_id not in group["members"]:
                raise ValueError(f"Physical occurrence is absent from group: {component_id}")
            mesh = model_dir / "collision_meshes" / f"{definition}.stl"
            if not mesh.is_file():
                raise ValueError(f"Missing source-exported collision mesh: {mesh}")
            parts[definition] = Part(part_id=definition, asset_paths={"stl": str(mesh)}, metadata={"mesh_scale_to_m": 0.001})
            position = tuple(float(v) for v in geom.get("pos", "0 0 0").split())
            w, x, y, z = (float(v) for v in geom.get("quat", "1 0 0 0").split())
            local = Pose(position_m=position, orientation_xyzw=(x, y, z, w))
            parent = trajectories[group["group_id"]]
            poses = tuple(compose_pose(parent=p, child=local) for p in parent.poses)
            components.append(Component(component_id=component_id, part_id=definition, initial_pose=poses[0]))
            traces.append(Trajectory(component_id=component_id, times_s=parent.times_s, poses=poses))
            group_for[component_id] = group["group_id"]
    expected = {f"node/{mapping['root_definition_id']}/{name}" for name in (
        "base", "guard", "crank", "coupler", "rocker", "pin_a", "pin_b", "pin_c", "pin_d",
    )}
    if set(group_for) != expected:
        raise ValueError("The collision scope must contain all nine physical occurrences")
    physical = AssemblyModel(assembly_id=assembly.assembly_id + ".physical", parts=tuple(parts.values()), components=tuple(components))
    recorded = replace(motion, assembly_id=physical.assembly_id, trajectories=tuple(traces))
    pairs = tuple(combinations(sorted(expected), 2))
    moving = tuple(pair for pair in pairs if group_for[pair[0]] != group_for[pair[1]])
    fixed = tuple(pair for pair in pairs if group_for[pair[0]] == group_for[pair[1]])
    return physical, recorded, moving, fixed
