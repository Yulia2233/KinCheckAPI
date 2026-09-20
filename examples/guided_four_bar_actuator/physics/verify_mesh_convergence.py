"""Independent closed-triangle integration against the validated BREP tensor.

This reads only definition-local BREP bytes whose digest is already recorded by
verify_conversion.py's explicit legacy-SDK validation. No placement is decoded
or repaired with the current SDK.
"""

from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np
import trimesh
from kincheckapi.dynamics import PhysicsManifest

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = PhysicsManifest.from_dict(
        json.loads((ROOT / "physics/physics-manifest.json").read_text())
    )
    package = ROOT / "model/out/guided_four_bar_actuator.scadpkg"
    assert hashlib.sha256(package.read_bytes()).hexdigest() == manifest.source_sha256
    expected = manifest.definitions["coupler"]
    sha = expected.provenance["brep_sha256"]
    with zipfile.ZipFile(package) as archive:
        source = json.loads(archive.read("package.json"))
        blob = next(
            b for b in source["blobs"] if b["sha256"].removeprefix("sha256:") == sha
        )
        raw = archive.read(blob["storage"]["path"])
    assert hashlib.sha256(raw).hexdigest() == sha
    from simplecadapi.artifacts.brep import read_brep_solid
    from simplecadapi.exporter import tessellate_solid

    shape = read_brep_solid(raw).wrapped
    rows = []
    for chord, angle in ((0.15, 15), (0.05, 8), (0.01, 2)):
        vertices, faces = tessellate_solid(
            shape,
            linear_deflection=chord,
            angular_deflection_degrees=angle,
            relative=False,
        )
        mesh = trimesh.Trimesh(vertices=vertices * 0.001, faces=faces, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent
        mesh.density = 7850
        m = mesh.mass_properties
        rows.append(
            {
                "chord_mm": chord,
                "angular_deg": angle,
                "triangles": len(faces),
                "watertight": True,
                "mass_kg": float(m.mass),
                "com_m": m.center_mass.tolist(),
                "inertia_com_kg_m2": m.inertia.tolist(),
                "mass_relative_error": abs(m.mass - expected.mass_kg)
                / expected.mass_kg,
                "inertia_relative_error": float(
                    np.linalg.norm(m.inertia - expected.inertia_com_kg_m2)
                    / np.linalg.norm(expected.inertia_com_kg_m2)
                ),
            }
        )
    for key in ("mass_relative_error", "inertia_relative_error"):
        assert rows[2][key] < rows[1][key] < rows[0][key]
        assert rows[2][key] < 0.001
    out = {
        "passed": True,
        "operation": "verify_brep_mesh_convergence",
        "source_sha256": manifest.source_sha256,
        "brep_sha256": sha,
        "kind": "mesh_estimate; never replaces BREP truth",
        "frozen_finest_relative_error_limit": 0.001,
        "rows": rows,
    }
    (ROOT / "physics/mesh-convergence.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
