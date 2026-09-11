"""Export the four-bar linkage product package as MJCF."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import simplecadapi as scad

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collision_policy import COLLISION_EXCLUSION_COMPONENT_PAIRS  # noqa: E402

CASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = CASE_DIR
PACKAGE_PATH = CASE_DIR / "four_bar_linkage.scadpkg"
MJCF_PATH = OUT_DIR / "four_bar_linkage.xml"
MAPPING_PATH = OUT_DIR / "four_bar_linkage.mapping.json"
MESH_DIR = OUT_DIR / "four_bar_linkage_meshes"


def _write_collision_policy(mapping_path: Path) -> tuple[tuple[str, str], ...]:
    """Persist source-level joint interface exclusions beside the MJCF."""

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    groups = tuple(mapping.get("groups", ()))
    group_ids = {"ground": str(mapping["grounded_group_id"])}
    for component_id in ("crank", "coupler", "rocker"):
        matches = [
            str(item["group_id"])
            for item in groups
            if str(item.get("group_id", "")).endswith(f"/{component_id}")
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Cannot resolve one MJCF group for source component {component_id!r}"
            )
        group_ids[component_id] = matches[0]
    exclusions = tuple(
        tuple(sorted((group_ids[a], group_ids[b])))
        for a, b in COLLISION_EXCLUSION_COMPONENT_PAIRS
    )
    mapping["collision_exclusions"] = [list(pair) for pair in sorted(exclusions)]
    mapping_path.write_text(
        json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return exclusions


def main() -> None:
    """Compile the captured `.scadpkg` into an MJCF model."""

    if not PACKAGE_PATH.is_file():
        raise FileNotFoundError(f"Run main.py first: {PACKAGE_PATH}")
    report = scad.exporter.export_product_package_to_mjcf(
        data=PACKAGE_PATH,
        output_path=MJCF_PATH,
        mapping_path=MAPPING_PATH,
        mesh_directory=MESH_DIR,
        linear_deflection=0.1,
    )
    exclusions = _write_collision_policy(MAPPING_PATH)
    print("model", report.output_path)
    print("mjcf_bodies", report.body_count)
    print("mjcf_joints", report.joint_count)
    print("mjcf_equalities", report.equality_count)
    print("mjcf_closures", report.closure_count)
    print("collision_exclusions", exclusions)

if __name__ == "__main__":
    main()
