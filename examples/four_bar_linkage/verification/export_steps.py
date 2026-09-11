"""Export both retained CAD packages to AP242 STEP and inspect the files.

Run with a Python environment containing SimpleCADAPI and OpenCASCADE.
The captured packages are the geometry source; model dimensions are unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from simplecadapi.exporter.step import export_product_package_to_step
from simplecadapi.inspect import brep


CASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = CASE_DIR / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    evidence = {}
    for variant in ("before", "after"):
        package = CASE_DIR / f"model_{variant}" / "four_bar_linkage.scadpkg"
        destination = OUTPUT_DIR / f"four_bar_{variant}.step"
        report = export_product_package_to_step(data=package, output_path=destination)
        summary = brep.inspect_step_rsummary(path=destination)
        if not summary["valid"] or summary["body_count"] != 8 or report.occurrence_count != 8:
            raise RuntimeError(f"{variant}: expected a valid STEP containing four bars and four bolts")
        evidence[variant] = {"export": report.to_dict(), "inspection": summary}
        print(f"{variant}: {report.schema}, {report.occurrence_count} occurrences, {destination.stat().st_size} bytes")
    (OUTPUT_DIR / "step_export.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
