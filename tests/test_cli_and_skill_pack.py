from __future__ import annotations

import json
from pathlib import Path

from kincheckapi.cli import EXIT_INPUT_ERROR, EXIT_OK, EXIT_VERIFICATION_FAILED, main
from kincheckapi.auto_tools.skill_pack import build


def test_doctor_json_has_stable_contract(capsys) -> None:
    exit_code = main(["doctor", "--format", "json"])
    output = json.loads(capsys.readouterr().out)
    assert exit_code in {EXIT_OK, 3}
    assert output["operation"] == "doctor"
    assert output["status"] in {"passed", "capability_failed"}
    assert "checks" in output
    assert "python" in output


def test_verify_pass_and_fail_exit_codes(tmp_path: Path, capsys) -> None:
    script = tmp_path / "verify.py"
    script.write_text(
        "def verify(model_dir):\n"
        "    return {'passed': model_dir.name == 'good', 'status': 'passed' if model_dir.name == 'good' else 'failed'}\n",
        encoding="utf-8",
    )
    good = tmp_path / "good"
    bad = tmp_path / "bad"
    good.mkdir()
    bad.mkdir()

    assert main(["verify", str(good), "--script", str(script), "--format", "json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["status"] == "passed"
    assert main(["verify", str(bad), "--script", str(script), "--format", "json"]) == EXIT_VERIFICATION_FAILED
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_verify_requires_public_verify_function(tmp_path: Path, capsys) -> None:
    script = tmp_path / "verify.py"
    script.write_text("VALUE = True\n", encoding="utf-8")
    model = tmp_path / "model"
    model.mkdir()
    assert main(["verify", str(model), "--script", str(script), "--format", "json"]) == EXIT_INPUT_ERROR
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "AttributeError"


def test_skill_pack_builds_standard_bundle_and_adapters(tmp_path: Path) -> None:
    output = tmp_path / "dist"
    results = build(language="both", output_root=output, archive=True, adapters=True)
    assert (output / "kincheckapi/SKILL.md").is_file()
    assert (output / "kincheckapi/references/docs/README.md").is_file()
    assert (output / "kincheckapi-zh/SKILL.md").is_file()
    assert (output / "kincheckapi.tar.gz").is_file()
    assert (output / "kincheckapi-zh.tar.gz").is_file()
    assert (output / "adapters/claude-code/.claude-plugin/plugin.json").is_file()
    assert (output / "adapters/claude-code/skills/kincheckapi/SKILL.md").is_file()
    assert (output / "adapters/codex/kincheckapi/SKILL.md").is_file()
    assert (output / "adapters/gemini/kincheckapi/SKILL.md").is_file()
    assert (output / "adapters/cursor-opencode/kincheckapi/SKILL.md").is_file()
    assert results
    assert not list((output / "kincheckapi").rglob("src"))


def test_wheel_skill_sources_match_checked_in_sources() -> None:
    root = Path(__file__).resolve().parents[1]
    for language, source_name, package_name in (
        ("en", "skill", "_skill_en"),
        ("zh", "skill_zh", "_skill_zh"),
    ):
        source_files = sorted(
            path.relative_to(root / source_name)
            for path in (root / source_name).rglob("*.md")
        )
        package_root = root / "src" / "kincheckapi" / package_name
        package_files = sorted(path.relative_to(package_root) for path in package_root.rglob("*.md"))
        assert package_files == source_files, language
        for relative in source_files:
            assert (package_root / relative).read_text(encoding="utf-8") == (
                root / source_name / relative
            ).read_text(encoding="utf-8")
