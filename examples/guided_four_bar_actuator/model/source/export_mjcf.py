"""Export the captured package to the KinCheckAPI model directory."""
from __future__ import annotations

from pathlib import Path

import simplecadapi as scad

HERE = Path(__file__).resolve().parents[1]
PACKAGE = HERE / "out" / "guided_four_bar_actuator.scadpkg"
MODEL = HERE


def main() -> None:
    if not PACKAGE.is_file():
        raise FileNotFoundError(f"Run main.py first: {PACKAGE}")
    report = scad.exporter.export_product_package_to_mjcf(
        data=PACKAGE,
        output_path=MODEL / "scene.xml",
        mapping_path=MODEL / "scene.mapping.json",
        mesh_directory=MODEL / "meshes",
        linear_deflection=0.02,
        angular_deflection_degrees=10.0,
    )
    print(f"mjcf={report.output_path} bodies={report.body_count} joints={report.joint_count} equalities={report.equality_count} closures={report.closure_count}")


if __name__ == "__main__":
    main()
