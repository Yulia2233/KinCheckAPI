import json
import os
from pathlib import Path
import subprocess
import sys

from kincheckapi.gui import GuiScenarioDocument, GuiSimulationService, export_verification_bundle, generate_verification_script


def multibody_document() -> GuiScenarioDocument:
    return GuiScenarioDocument(
        document_id="gui-test",
        analysis="multibody",
        scenario={
            "states": [{"joint_id": "joint", "position": [0.0], "velocity": [0.0], "acceleration": [0.0]}],
            "mass_matrix": [[1.0]],
            "force_vector": [1.0],
            "duration_s": 0.1,
            "sample_period_s": 0.05,
            "scenario_id": "gui-test-case",
        },
    )


def test_gui_scenario_round_trip_and_service_result():
    document = GuiScenarioDocument.from_dict(json.loads(json.dumps(multibody_document().to_dict())))
    assert document.content_sha256 == multibody_document().content_sha256
    result = GuiSimulationService().run(document=document)
    assert result.passed, result.to_dict()
    assert result.payload["load_history"]["schema_version"] == "kincheck.dynamics-history/1.0"


def test_gui_service_rejects_empty_matrix_and_does_not_import_viewer():
    document = GuiScenarioDocument(document_id="empty", analysis="scenario_matrix", cases=({"case_id": "x", "scenario": multibody_document().scenario},))
    result = GuiSimulationService().run(document=document)
    assert result.passed
    assert "viewer" not in GuiSimulationService.__module__


def test_gui_exports_runnable_verification_bundle(tmp_path):
    document = multibody_document()
    bundle = export_verification_bundle(document=document, output_dir=tmp_path / "verification")
    script = bundle / "verify.py"
    assert "import viewer" not in generate_verification_script().lower()
    completed = subprocess.run(
        [sys.executable, str(script), "--scenario", str(bundle / "scenario.json"), "--output", str(bundle / "result.json"), "--strict"],
        cwd=bundle,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")},
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads((bundle / "result.json").read_text())["passed"] is True
