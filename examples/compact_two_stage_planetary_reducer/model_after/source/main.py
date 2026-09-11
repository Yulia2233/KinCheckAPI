"""Build the unchanged reducer design and capture the corrected product package."""
from pathlib import Path
import sys
import simplecadapi as scad
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.setrecursionlimit(50000)
from assembly import build_two_stage_planetary_reducer_product
MODEL_DIR = Path(__file__).resolve().parents[1]
def main():
    result = build_two_stage_planetary_reducer_product()
    path = MODEL_DIR / "compact_two_stage_planetary_reducer.scadpkg"
    scad.capture(result, path)
    print(f"product_package={path}", flush=True)
if __name__ == "__main__":
    main()
