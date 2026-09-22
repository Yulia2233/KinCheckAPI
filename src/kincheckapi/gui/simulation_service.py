"""Headless service used by the native GUI and generated scripts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from ..dynamics_v07 import (
    ContactInterface,
    DynamicsScenarioCase,
    DynamicsScenarioMatrix,
    RigidDynamicsScenario,
    history_from_multibody_result,
    run_dynamics_cases,
    solve_contact_dynamics,
    solve_multibody_dynamics,
)
from ..physics_types import PhysicsReport
from ..assembly import assembly_from_dict
from ..kinematics import solve_motion
from ..scenario import (
    ComponentResultRequest,
    ComponentResultScope,
    JointResultRequest,
    JointValue,
    MotionProfile,
    PositionDriver,
    ProfilePoint,
    Scenario,
    SpeedDriver,
)
from .scenario_document import GuiScenarioDocument


def _report_payload(report: Any) -> dict[str, Any]:
    if hasattr(report, "to_dict"):
        value = report.to_dict()
        return dict(value) if isinstance(value, Mapping) else {"status": "failed", "passed": False, "value": value}
    return dict(report)


@dataclass(frozen=True, slots=True, kw_only=True)
class GuiRunResult:
    run_id: str
    document_id: str
    analysis: str
    status: str
    passed: bool
    payload: Mapping[str, Any]
    scenario_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "document_id": self.document_id,
            "analysis": self.analysis,
            "status": self.status,
            "passed": self.passed,
            "payload": dict(self.payload),
            "scenario_sha256": self.scenario_sha256,
        }


class GuiSimulationService:
    """Orchestrate typed public solvers without importing the Viewer."""

    _UNIMPLEMENTED_ANALYSES = {"scalar_dynamics", "static"}

    @staticmethod
    def _assembly(document: GuiScenarioDocument):
        raw_path = document.model.get("assembly_json") or document.model.get("path")
        if not raw_path:
            raise ValueError("GUI kinematics requires model.assembly_json or a JSON model path")
        path = Path(str(raw_path)).expanduser()
        if path.is_dir():
            path = path / "assembly.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        return assembly_from_dict(data=value)

    def _kinematic_scenario(self, document: GuiScenarioDocument) -> Scenario:
        value = document.scenario
        assembly = self._assembly(document)
        profile = lambda points: MotionProfile(points=tuple(ProfilePoint(time_s=float(p["time_s"]), value=float(p["value"])) for p in points), interpolation="linear")
        return Scenario(
            scenario_id=str(value.get("scenario_id", document.document_id)),
            assembly=assembly,
            initial_joint_positions=tuple(JointValue(joint_id=str(key), value=float(number)) for key, number in value.get("initial_joint_positions", {}).items()),
            initial_joint_velocities=tuple(JointValue(joint_id=str(key), value=float(number)) for key, number in value.get("initial_joint_velocities", {}).items()),
            position_drivers=tuple(PositionDriver(joint_id=str(item["joint_id"]), profile=profile(item["points"])) for item in value.get("position_drivers", ())),
            speed_drivers=tuple(SpeedDriver(joint_id=str(item["joint_id"]), profile=profile(item["points"])) for item in value.get("speed_drivers", ())),
            duration_s=value.get("duration_s"),
            sample_period_s=value.get("sample_period_s"),
            joint_result_requests=tuple(JointResultRequest(joint_id=str(item)) for item in value.get("joint_result_requests", ())),
            component_result_requests=tuple(ComponentResultRequest(component_id=str(item["component_id"]), connector_id=item.get("connector_id")) for item in value.get("component_result_requests", ())),
            component_result_scope=str(value.get("component_result_scope", "requested")),
        )

    def validate_document(self, document: GuiScenarioDocument) -> PhysicsReport:
        if not isinstance(document, GuiScenarioDocument):
            return PhysicsReport(operation="gui_validate_scenario", status="validation_failed", evidence={"reason": "GuiScenarioDocument required"})
        try:
            if document.analysis == "multibody":
                RigidDynamicsScenario.from_dict(document.scenario)
            elif document.analysis == "kinematics":
                self._kinematic_scenario(document)
            elif document.analysis == "contact":
                ContactInterface.from_dict(document.scenario["interface"])
                for name in ("times_s", "relative_gap_m", "relative_normal_velocity_m_s"):
                    if name not in document.scenario:
                        raise ValueError(f"contact scenario missing {name}")
            elif document.analysis == "scenario_matrix":
                matrix = DynamicsScenarioMatrix(
                    matrix_id=document.document_id,
                    cases=tuple(
                        DynamicsScenarioCase(
                            case_id=str(case["case_id"]),
                            scenario=RigidDynamicsScenario.from_dict(case["scenario"]),
                        )
                        for case in document.cases
                    ),
                )
                if not matrix.cases:
                    raise ValueError("scenario matrix cannot be empty")
            elif document.analysis in self._UNIMPLEMENTED_ANALYSES:
                return PhysicsReport(
                    operation="gui_validate_scenario",
                    status="capability_failed",
                    evidence={"analysis": document.analysis, "reason": "GUI adapter is not registered for this legacy request shape"},
                )
            else:
                raise ValueError(f"unsupported analysis {document.analysis}")
        except Exception as exc:
            return PhysicsReport(operation="gui_validate_scenario", status="validation_failed", evidence={"error_type": type(exc).__name__, "message": str(exc)})
        return PhysicsReport(operation="gui_validate_scenario", status="passed", evidence={"analysis": document.analysis, "scenario_sha256": document.content_sha256})

    def run(self, *, document: GuiScenarioDocument, run_id: str = "gui-run") -> GuiRunResult:
        validation = self.validate_document(document)
        if not validation.passed:
            payload = _report_payload(validation)
            return GuiRunResult(run_id=run_id, document_id=document.document_id, analysis=document.analysis, status=str(payload.get("status", "failed")), passed=False, payload=payload, scenario_sha256=document.content_sha256)
        if document.analysis == "multibody":
            result = solve_multibody_dynamics(scenario=RigidDynamicsScenario.from_dict(document.scenario))
            payload = result.to_dict()
            payload["load_history"] = history_from_multibody_result(result=result).to_dict()
        elif document.analysis == "kinematics":
            result = solve_motion(scenario=self._kinematic_scenario(document))
            payload = result.to_dict()
        elif document.analysis == "contact":
            scenario = document.scenario
            result = solve_contact_dynamics(
                interface=ContactInterface.from_dict(scenario["interface"]),
                times_s=scenario["times_s"],
                relative_gap_m=scenario["relative_gap_m"],
                relative_normal_velocity_m_s=scenario["relative_normal_velocity_m_s"],
                relative_tangential_velocity_m_s=scenario.get("relative_tangential_velocity_m_s"),
            )
            payload = result.to_dict()
        elif document.analysis == "scenario_matrix":
            matrix = DynamicsScenarioMatrix(
                matrix_id=document.document_id,
                cases=tuple(DynamicsScenarioCase(case_id=str(case["case_id"]), scenario=RigidDynamicsScenario.from_dict(case["scenario"])) for case in document.cases),
            )
            payload = run_dynamics_cases(matrix=matrix).to_dict()
        else:  # validation already returned capability_failed for these paths
            payload = {"status": "capability_failed", "passed": False}
        return GuiRunResult(run_id=run_id, document_id=document.document_id, analysis=document.analysis, status=str(payload.get("status", "failed")), passed=bool(payload.get("passed", False)), payload=payload, scenario_sha256=document.content_sha256)

    @staticmethod
    def save_result(result: GuiRunResult, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(result.to_dict(), handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
