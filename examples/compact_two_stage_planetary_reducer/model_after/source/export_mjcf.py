"""Export the validated reducer package through the canonical SDK exporter."""
from pathlib import Path
from simplecadapi.exporter.mjcf import export_product_package_to_mjcf
MODEL_DIR = Path(__file__).resolve().parents[1]
def main():
    report = export_product_package_to_mjcf(data=MODEL_DIR / "compact_two_stage_planetary_reducer.scadpkg", output_path=MODEL_DIR / "scene.xml", mapping_path=MODEL_DIR / "scene.mapping.json", mesh_directory=MODEL_DIR / "meshes")
    print(report, flush=True)
if __name__ == "__main__":
    main()
