"""Portable GUI scenario requests.

This module contains no Tk imports so it can be used by headless CI and by
generated verification scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


GUI_SCENARIO_SCHEMA_VERSION = "kincheck.gui-scenario/1.0"
SUPPORTED_ANALYSES = frozenset({
    "kinematics",
    "scalar_dynamics",
    "multibody",
    "contact",
    "scenario_matrix",
    "static",
})


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class GuiScenarioDocument:
    """A saved request document, never a result or an implicit solver state."""

    document_id: str
    analysis: str
    model: Mapping[str, Any] = field(default_factory=dict)
    scenario: Mapping[str, Any] = field(default_factory=dict)
    cases: tuple[Mapping[str, Any], ...] = ()
    checks: tuple[Mapping[str, Any], ...] = ()
    run_options: Mapping[str, Any] = field(default_factory=lambda: {"strict": True})
    schema_version: str = GUI_SCENARIO_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != GUI_SCENARIO_SCHEMA_VERSION:
            raise ValueError(f"Unsupported GUI scenario schema: {self.schema_version!r}")
        if not self.document_id.strip():
            raise ValueError("document_id must be non-empty")
        if self.analysis not in SUPPORTED_ANALYSES:
            raise ValueError(f"Unsupported GUI analysis: {self.analysis!r}")
        model = dict(self.model)
        if model.get("path") is not None and not isinstance(model.get("path"), str):
            raise ValueError("model.path must be a string")
        cases = tuple(dict(case) for case in self.cases)
        case_ids = [str(case.get("case_id", "")) for case in cases]
        if any(not case_id for case_id in case_ids) or len(set(case_ids)) != len(case_ids):
            raise ValueError("cases require unique non-empty case_id values")
        if self.analysis == "scenario_matrix" and not cases:
            raise ValueError("scenario_matrix requires at least one case")
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "scenario", dict(self.scenario))
        object.__setattr__(self, "cases", cases)
        object.__setattr__(self, "checks", tuple(dict(check) for check in self.checks))
        object.__setattr__(self, "run_options", dict(self.run_options))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "document_id": self.document_id,
            "analysis": self.analysis,
            "model": _canonical(self.model),
            "scenario": _canonical(self.scenario),
            "cases": _canonical(self.cases),
            "checks": _canonical(self.checks),
            "run_options": _canonical(self.run_options),
        }

    @property
    def content_sha256(self) -> str:
        return _digest(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "GuiScenarioDocument":
        return cls(
            schema_version=str(value.get("schema_version", "")),
            document_id=str(value.get("document_id", "")),
            analysis=str(value.get("analysis", "")),
            model=value.get("model", {}),
            scenario=value.get("scenario", {}),
            cases=tuple(value.get("cases", ())),
            checks=tuple(value.get("checks", ())),
            run_options=value.get("run_options", {"strict": True}),
        )

    @classmethod
    def read(cls, path: str | Path) -> "GuiScenarioDocument":
        value = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        if not isinstance(value, Mapping):
            raise ValueError("GUI scenario JSON must contain an object")
        return cls.from_dict(value)

    def write(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.to_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return destination
