"""Use KinCheckAPI to convert the ex12 CADIR MJCF export.

The CADIR export is already present under ``model_after/``. This example
converts it into the backend-independent ``AssemblyModel`` used by the rest of
KinCheckAPI. It does not rebuild the CADIR package or run motion simulation.
"""

from __future__ import annotations

from pathlib import Path
import sys


CASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = CASE_DIR.parents[1]
MJCF_DIR = CASE_DIR / "model_after"
XML_PATH = MJCF_DIR / "four_bar_linkage.xml"
MAPPING_PATH = MJCF_DIR / "four_bar_linkage.mapping.json"

# Make the example runnable from the KinCheckAPI repository checkout.
sys.path.insert(0, str(REPO_ROOT / "src"))

from kincheckapi.cadir import convert_mjcf  # noqa: E402


def main() -> None:
    """Convert CADIR MJCF files and inspect the resulting AssemblyModel."""

    converted = convert_mjcf(
        xml_path=XML_PATH,
        mapping_path=MAPPING_PATH,
        asset_root=MJCF_DIR,
    )
    assembly = converted.assembly

    print("AssemblyModel")
    print(f"  assembly_id: {assembly.assembly_id}")
    print(f"  parts: {len(assembly.parts)}")
    print(f"  components: {len(assembly.components)}")
    print(f"  joints: {len(assembly.joints)}")
    print(f"  closures: {len(assembly.closures)}")
    print(f"  couplings: {len(assembly.couplings)}")
    print(f"  grounds: {len(assembly.grounds)}")
    print(f"  collision exclusions: {len(assembly.collision_exclusions)}")

    print("\nComponents")
    for component in assembly.components:
        part = assembly.get_part(part_id=component.part_id)
        stl_path = None if part is None else part.asset_paths.get("stl")
        print(
            f"  {component.component_id}: "
            f"part={component.part_id}, "
            f"body={component.metadata.get('xml_body_name')}, "
            f"clearance_stl={stl_path}"
        )

    print("\nJoints")
    for joint in assembly.joints:
        print(
            f"  {joint.joint_id}: "
            f"type={joint.joint_type.value}, "
            f"limit={joint.limit}, "
            f"parent={joint.connector_a.component_id}, "
            f"child={joint.connector_b.component_id}"
        )

    print("\nClosures")
    for closure in assembly.closures:
        print(
            f"  {closure.closure_id}: "
            f"type={closure.constraint.constraint_type}, "
            f"sites={closure.constraint.metadata.get('xml_site_names')}"
        )

    print("\nSource map")
    for key in (
        "source_group_id_to_xml_body",
        "source_joint_id_to_xml_name",
        "source_site_id_to_xml_name",
        "source_closure_id_to_xml_equality",
    ):
        print(f"  {key}: {converted.source_map[key]}")


if __name__ == "__main__":
    main()
