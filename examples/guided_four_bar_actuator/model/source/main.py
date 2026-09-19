"""Build and capture the guided four-bar actuator CADIR package."""
from __future__ import annotations

import time
import json
from pathlib import Path

import simplecadapi as scad
from simplecadapi.inspect import brep

from assembly import build_guided_four_bar_actuator, _durable_parts

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "out"
PACKAGE = OUT / "guided_four_bar_actuator.scadpkg"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    result = build_guided_four_bar_actuator()
    build_s = time.perf_counter() - start
    leaves = _durable_parts()
    geometry = []
    for leaf in leaves:
        report = brep.inspect_shape_rbrepinspection(leaf.part.body.wrapped)
        if not report.valid or report.volume <= 0 or report.counts.get("solid") != 1 or report.counts.get("open_shell") != 0:
            raise ValueError(f"Invalid physical part: {leaf.part.part_id}: {report.counts}")
        geometry.append({"part_id": leaf.part.part_id, "valid": report.valid,
                         "volume_mm3": report.volume, "bounding_box_mm": report.bounding_box,
                         "counts": report.counts})
    (OUT / "geometry_validation.json").write_text(json.dumps(geometry, indent=2, sort_keys=True) + "\n")
    scad.capture(result, PACKAGE, include_scene=False)
    # Independent per-definition meshes preserve physical hardware checks even
    # when MJCF combines fixed occurrences into a single rigid group.
    for leaf in leaves:
        leaf_path = OUT / "parts" / f"{leaf.part.part_id}.scadpkg"
        leaf_path.parent.mkdir(parents=True, exist_ok=True)
        scad.capture(leaf, leaf_path, include_scene=False)
        target = HERE / "collision_meshes" / f"{leaf.part.part_id}.stl"
        target.parent.mkdir(parents=True, exist_ok=True)
        scad.exporter.export_product_package_to_stl(leaf_path, target, linear_deflection=0.02, angular_deflection_degrees=10.0)
    print(f"[stage] build_s={build_s:.2f} package={PACKAGE} bytes={PACKAGE.stat().st_size}")


if __name__ == "__main__":
    main()
