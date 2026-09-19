"""Complete guided four-bar actuator assembly with fixed service hardware."""
from __future__ import annotations

import math
from pathlib import Path

import simplecadapi as scad

from base_plate import make_base_part
from dimensions import (
    CLOSURE_ANGLE_LIMIT,
    LOWER_LINK_CENTER_Z, COUPLER_CENTER_Z,
    GROUND_PIN_BOTTOM_Z, GROUND_PIN_HEAD_BASE_Z,
    LINK_PIN_BOTTOM_Z, LINK_PIN_HEAD_BASE_Z,
    COUPLER_ASSEMBLED_ANGLE_DEG,
    COUPLER_LENGTH,
    CRANK_ASSEMBLED_ANGLE_DEG,
    CRANK_LENGTH,
    CRANK_PIVOT,
    GROUND_LENGTH,
    ROCKER_ASSEMBLED_ANGLE_DEG,
    ROCKER_LENGTH,
    ROCKER_PIVOT,
)
from guard import make_guard_part
from link_bar import make_link_part
from pivot_bolt import make_pivot_bolt_part

HERE = Path(__file__).resolve().parent
CACHE = scad.CachePolicy(root=HERE.parent / "out" / ".cache")
MATERIAL = scad.make_material_rmaterial(material_id="actuator_steel", name="Actuator steel", density=7.85e-6, density_unit="kg/mm^3", color=(0.55, 0.58, 0.62))
BOLT_MATERIAL = scad.make_material_rmaterial(material_id="actuator_pin", name="Hardened pivot pins", density=7.85e-6, density_unit="kg/mm^3", color=(0.18, 0.20, 0.23))


def _rotation_placement(origin: tuple[float, float], angle_deg: float) -> scad.Placement:
    radians = math.radians(angle_deg)
    cos_a, sin_a = math.cos(radians), math.sin(radians)
    return scad.make_placement_rplacement(
        origin=(origin[0], origin[1], 0.0),
        x_axis=(cos_a, sin_a, 0.0),
        y_axis=(-sin_a, cos_a, 0.0),
    )


def _durable_parts():
    @scad.part(id="base", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_base() -> scad.Part:
        return make_base_part(material=MATERIAL)

    @scad.part(id="crank", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_crank() -> scad.Part:
        return make_link_part("crank", CRANK_LENGTH, center_z=LOWER_LINK_CENTER_Z, material=MATERIAL)

    @scad.part(id="coupler", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_coupler() -> scad.Part:
        return make_link_part("coupler", COUPLER_LENGTH, center_z=COUPLER_CENTER_Z, material=MATERIAL)

    @scad.part(id="rocker", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_rocker() -> scad.Part:
        return make_link_part("rocker", ROCKER_LENGTH, center_z=LOWER_LINK_CENTER_Z, material=MATERIAL)

    @scad.part(id="ground_pin", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_pin() -> scad.Part:
        return make_pivot_bolt_part("ground_pin", GROUND_PIN_HEAD_BASE_Z - GROUND_PIN_BOTTOM_Z, head_base_z=GROUND_PIN_HEAD_BASE_Z, seat_z=2.0, material=BOLT_MATERIAL)

    @scad.part(id="link_pin", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_link_pin() -> scad.Part:
        return make_pivot_bolt_part("link_pin", LINK_PIN_HEAD_BASE_Z - LINK_PIN_BOTTOM_Z, head_base_z=LINK_PIN_HEAD_BASE_Z, seat_z=LOWER_LINK_CENTER_Z + 2.0, material=BOLT_MATERIAL)

    @scad.part(id="guard", revision="1.1.1", cache=CACHE, project_root=HERE)
    def build_guard() -> scad.Part:
        return make_guard_part(material=MATERIAL)

    return build_base(), build_crank(), build_coupler(), build_rocker(), build_pin(), build_link_pin(), build_guard()


def build_guided_four_bar_actuator() -> scad.AssemblyBuildResult:
    base_r, crank_r, coupler_r, rocker_r, pin_r, link_pin_r, guard_r = _durable_parts()
    definitions = (base_r, crank_r, coupler_r, rocker_r, pin_r, link_pin_r, guard_r)

    @scad.assemble(
        id="guided_four_bar_actuator",
        revision="1.1.1",
        definitions=definitions,
        cache=CACHE,
        project_root=HERE,
    )
    def build() -> scad.Assembly:
        assembly = scad.make_assembly_rassembly(
            assembly_id="guided_four_bar_actuator",
            name="Guided four-bar service actuator",
        )
        parts = {result.part.part_id: result.part for result in definitions}
        placements = {
            "base": scad.identity_placement_rplacement(),
            "crank": _rotation_placement(CRANK_PIVOT, CRANK_ASSEMBLED_ANGLE_DEG),
            "rocker": _rotation_placement(ROCKER_PIVOT, ROCKER_ASSEMBLED_ANGLE_DEG),
            "coupler": _rotation_placement((CRANK_LENGTH, 0.0), COUPLER_ASSEMBLED_ANGLE_DEG),
            "guard": scad.identity_placement_rplacement(),
        }
        for component_id in ("base", "crank", "rocker", "coupler", "guard"):
            assembly = scad.add_component_rassembly(
                assembly=assembly, item=parts[component_id], component_id=component_id,
                placement=placements[component_id], name=component_id.replace("_", " ").title(),
            )
        assembly = scad.add_fixed_constraint_rassembly(
            assembly=assembly, constraint_id="guard_to_base",
            connector_a=scad.make_connector_ref_rconnectorref("base", "guard_mount"),
            connector_b=scad.make_connector_ref_rconnectorref("guard", "mount"),
        )
        # One pin per moving pivot is fixed to its host link; pins remain physical geometry.
        pin_specs = (
            ("pin_a", "base", "pivot_a", (0.0, 0.0)),
            ("pin_d", "base", "pivot_d", ROCKER_PIVOT),
            ("pin_b", "crank", "pivot_b", (CRANK_LENGTH, 0.0)),
        )
        for pin_id, host_id, host_connector, local_xy in pin_specs:
            host = placements[host_id]
            world = scad.make_placement_rplacement(
                origin=(host.origin[0] + local_xy[0], host.origin[1] + local_xy[1], 0.0)
            )
            assembly = scad.add_component_rassembly(
                assembly=assembly, item=parts["link_pin" if pin_id == "pin_b" else "ground_pin"], component_id=pin_id,
                placement=world, name=pin_id.replace("_", " ").title(),
            )
            assembly = scad.add_fixed_constraint_rassembly(
                assembly=assembly, constraint_id=f"{pin_id}_fixed",
                connector_a=scad.make_connector_ref_rconnectorref(host_id, host_connector),
                connector_b=scad.make_connector_ref_rconnectorref(pin_id, "axis"),
            )
        rocker_placement = placements["rocker"]
        tip = (
            rocker_placement.origin[0] + ROCKER_LENGTH * rocker_placement.x_axis[0],
            rocker_placement.origin[1] + ROCKER_LENGTH * rocker_placement.x_axis[1],
        )
        assembly = scad.add_component_rassembly(
            assembly=assembly, item=parts["link_pin"], component_id="pin_c",
            placement=scad.make_placement_rplacement(origin=(tip[0], tip[1], 0.0)),
            name="Tip pivot pin",
        )
        assembly = scad.add_fixed_constraint_rassembly(
            assembly=assembly, constraint_id="pin_c_fixed",
            connector_a=scad.make_connector_ref_rconnectorref("rocker", "pivot_b"),
            connector_b=scad.make_connector_ref_rconnectorref("pin_c", "axis"),
        )
        assembly = scad.ground_component_rassembly(assembly=assembly, component_id="base")
        assembly = scad.add_revolute_constraint_rassembly(
            assembly=assembly, constraint_id="crank_to_ground",
            connector_a=scad.make_connector_ref_rconnectorref("base", "pivot_a"),
            connector_b=scad.make_connector_ref_rconnectorref("crank", "pivot_a"),
            angle_limit=scad.make_scalar_limit_rscalarlimit(lower_value=-45.0, upper_value=85.0),
        )
        assembly = scad.add_revolute_constraint_rassembly(
            assembly=assembly, constraint_id="rocker_to_ground",
            connector_a=scad.make_connector_ref_rconnectorref("base", "pivot_d"),
            connector_b=scad.make_connector_ref_rconnectorref("rocker", "pivot_a"),
            angle_limit=scad.make_scalar_limit_rscalarlimit(lower_value=-45.0, upper_value=85.0),
        )
        assembly = scad.add_revolute_constraint_rassembly(
            assembly=assembly, constraint_id="coupler_to_crank",
            connector_a=scad.make_connector_ref_rconnectorref("crank", "pivot_b"),
            connector_b=scad.make_connector_ref_rconnectorref("coupler", "pivot_a"),
            angle_limit=scad.make_scalar_limit_rscalarlimit(lower_value=-180.0, upper_value=180.0),
        )
        assembly = scad.add_revolute_constraint_rassembly(
            assembly=assembly, constraint_id="coupler_to_rocker",
            connector_a=scad.make_connector_ref_rconnectorref("rocker", "pivot_b"),
            connector_b=scad.make_connector_ref_rconnectorref("coupler", "pivot_b"),
            angle_limit=scad.make_scalar_limit_rscalarlimit(
                lower_value=CLOSURE_ANGLE_LIMIT[0], upper_value=CLOSURE_ANGLE_LIMIT[1]
            ),
        )
        assembly = scad.set_public_connector_rassembly(
            assembly=assembly, public_connector_id="crank_input_axis",
            source_component_id="crank", source_connector_id="pivot_a",
            name="Crank input axis",
        )
        solved = scad.solve_assembly_constraints_rassembly(assembly=assembly, strict=True)
        report = solved._get_runtime("constraint_report")
        print(
            f"guided_four_bar_solved: components={len(solved.component_ids())} "
            f"constraints={len(solved.constraint_ids())} "
            f"residuals_ok={all(item['within_tolerance'] for item in report['residuals'])}"
        )
        return solved

    return build()
