from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

from kincheckapi.assembly import create_assembly, validate_assembly, validate_topology
from kincheckapi.checks import CheckSpec, run_checks
from kincheckapi.kinematics import solve_motion
from kincheckapi.result import ConstraintResidual, MotionResult
from kincheckapi.scenario import (
    add_joint_speed_driver,
    create_scenario,
    request_joint_result,
    set_run_duration,
    set_sample_period,
    validate_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skill_zh"


def test_generated_skill_api_docs_are_current() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/generate_skill_api_docs.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_skill_markdown_local_links_resolve() -> None:
    missing: list[str] = []
    link_pattern = re.compile(r"\[[^]]*\]\(([^)]+)\)")
    for source in SKILL_ROOT.rglob("*.md"):
        for target in link_pattern.findall(source.read_text(encoding="utf-8")):
            target = target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (source.parent / target).resolve().exists():
                missing.append(f"{source.relative_to(ROOT)} -> {target}")
    assert not missing, "\n".join(missing)


def test_skill_example_constraint_parameter_is_executable() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert 'parameters={"position_tolerance_m": 1e-6}' in skill_text
    assert "maximum_position_residual_m" not in skill_text

    assembly = create_assembly(assembly_id="assembly.skill-doc-smoke")
    motion = MotionResult(
        scenario_id="scenario.skill-doc-smoke",
        assembly_id=assembly.assembly_id,
        status="completed",
        start_time_s=0.0,
        end_time_s=0.0,
        sample_times_s=(0.0,),
        constraint_residuals=(
            ConstraintResidual(
                constraint_id="constraint.skill-doc-smoke",
                time_s=0.0,
                position_residual_m=0.0,
                orientation_residual_rad=0.0,
            ),
        ),
    )
    suite = run_checks(
        assembly=assembly,
        motion_result=motion,
        checks=(
            CheckSpec(
                check_id="constraints",
                check_type="constraint_residuals",
                parameters={"position_tolerance_m": 1e-6},
            ),
        ),
    )
    assert suite.passed


def test_skill_top_level_ex3_example_completes_and_passes(ex3_assembly) -> None:
    assert validate_assembly(assembly=ex3_assembly).passed
    assert validate_topology(assembly=ex3_assembly).passed

    scenario = create_scenario(
        scenario_id="ex3-verification",
        assembly=ex3_assembly,
    )
    scenario = add_joint_speed_driver(
        scenario=scenario,
        joint_id="joint.ex3.ground_crank",
        start_time_s=0.0,
        end_time_s=4.0,
        speed_rad_s_or_m_s=7e-4,
    )
    scenario = set_run_duration(scenario=scenario, duration_s=4.0)
    scenario = set_sample_period(scenario=scenario, period_s=1.0 / 30.0)
    scenario = request_joint_result(
        scenario=scenario,
        joint_id="joint.ex3.ground_crank",
    )
    assert validate_scenario(scenario=scenario).passed

    motion = solve_motion(scenario=scenario)
    assert motion.status in {"completed", "completed_with_warnings"}
    assert motion.sample_times_s

    suite = run_checks(
        assembly=ex3_assembly,
        scenario=scenario,
        motion_result=motion,
        checks=(
            CheckSpec(
                check_id="constraints",
                check_type="constraint_residuals",
                parameters={"position_tolerance_m": 1e-6},
            ),
        ),
    )
    assert suite.passed
