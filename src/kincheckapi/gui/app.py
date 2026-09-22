"""Standalone Tk desktop application for selecting and running scenarios."""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Any

from .scenario_document import GuiScenarioDocument, SUPPORTED_ANALYSES
from .simulation_service import GuiSimulationService
from .verification_export import export_verification_bundle


DEFAULT_MULTIBODY = {
    "states": [{"joint_id": "joint[0]", "position": [0.0], "velocity": [0.0], "acceleration": [0.0]}],
    "mass_matrix": [[1.0]],
    "force_vector": [1.0],
    "duration_s": 0.2,
    "sample_period_s": 0.05,
    "scenario_id": "gui-demo",
}


class KinCheckGui:
    """A small dependency-free native workbench; all calculations stay in the service."""

    def __init__(self, root: Any, *, scenario_path: str | Path | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.root.title("KinCheckAPI 0.8.0 — Dynamics Workbench")
        self.root.geometry("1100x760")
        self.service = GuiSimulationService()
        self.scenario_path: Path | None = None
        self.last_document: GuiScenarioDocument | None = None
        self.last_result: Any = None

        toolbar = ttk.Frame(root, padding=8)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Load", command=self.load).pack(side="left")
        ttk.Button(toolbar, text="Save", command=self.save).pack(side="left", padx=(4, 0))
        ttk.Button(toolbar, text="Validate", command=self.validate).pack(side="left", padx=(18, 0))
        ttk.Button(toolbar, text="Run", command=self.run).pack(side="left", padx=(4, 0))
        ttk.Button(toolbar, text="Export verifier", command=self.export_verifier).pack(side="left", padx=(4, 0))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="right")

        form = ttk.Frame(root, padding=(8, 0, 8, 8))
        form.pack(fill="x")
        ttk.Label(form, text="Document ID").grid(row=0, column=0, sticky="w")
        self.document_id = ttk.Entry(form, width=28)
        self.document_id.insert(0, "gui-scenario")
        self.document_id.grid(row=0, column=1, sticky="ew", padx=(6, 18))
        ttk.Label(form, text="Analysis").grid(row=0, column=2, sticky="w")
        self.analysis = ttk.Combobox(form, state="readonly", values=sorted(SUPPORTED_ANALYSES), width=22)
        self.analysis.set("multibody")
        self.analysis.grid(row=0, column=3, sticky="ew", padx=6)
        ttk.Label(form, text="Model path").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.model_path = ttk.Entry(form)
        self.model_path.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(8, 0))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        panes = ttk.Panedwindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        left = ttk.Frame(panes, padding=6)
        right = ttk.Frame(panes, padding=6)
        panes.add(left, weight=1)
        panes.add(right, weight=1)
        ttk.Label(left, text="Scenario JSON (or case array for scenario_matrix)").pack(anchor="w")
        self.scenario_text = tk.Text(left, wrap="none", undo=True)
        self.scenario_text.pack(fill="both", expand=True, pady=(4, 0))
        ttk.Label(right, text="Result / diagnostics").pack(anchor="w")
        self.result_text = tk.Text(right, wrap="none", state="disabled")
        self.result_text.pack(fill="both", expand=True, pady=(4, 0))

        self.canvas = tk.Canvas(root, height=150, background="#162029", highlightthickness=0)
        self.canvas.pack(fill="x", padx=8, pady=(0, 8))
        self._set_json(DEFAULT_MULTIBODY)
        if scenario_path:
            self._load_path(Path(scenario_path))

    def _set_json(self, value: Any) -> None:
        self.scenario_text.delete("1.0", "end")
        self.scenario_text.insert("1.0", json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True))

    def _get_document(self) -> GuiScenarioDocument:
        raw = json.loads(self.scenario_text.get("1.0", "end"))
        analysis = self.analysis.get()
        if analysis == "scenario_matrix":
            if not isinstance(raw, list):
                raise ValueError("scenario_matrix editor must contain an array of cases")
            cases = tuple(raw)
            scenario = {}
        else:
            if not isinstance(raw, dict):
                raise ValueError("scenario editor must contain an object")
            cases = ()
            scenario = raw
        return GuiScenarioDocument(
            document_id=self.document_id.get().strip() or "gui-scenario",
            analysis=analysis,
            model={"path": self.model_path.get().strip() or None},
            scenario=scenario,
            cases=cases,
        )

    def _show(self, value: Any) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True, default=str))
        self.result_text.configure(state="disabled")

    def _load_path(self, path: Path) -> None:
        document = GuiScenarioDocument.read(path)
        self.scenario_path = path
        self.document_id.delete(0, "end"); self.document_id.insert(0, document.document_id)
        self.analysis.set(document.analysis)
        self.model_path.delete(0, "end"); self.model_path.insert(0, str(document.model.get("path") or ""))
        self._set_json(list(document.cases) if document.analysis == "scenario_matrix" else document.scenario)
        self.status_var.set(f"Loaded {path.name}")

    def load(self) -> None:
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(filetypes=(("KinCheck scenario", "*.json"), ("All files", "*")))
        if not path:
            return
        try:
            self._load_path(Path(path))
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc))

    def save(self) -> None:
        from tkinter import filedialog, messagebox
        try:
            document = self._get_document()
            path = self.scenario_path or Path(f"{document.document_id}.json")
            selected = filedialog.asksaveasfilename(initialfile=path.name, defaultextension=".json", filetypes=(("KinCheck scenario", "*.json"),))
            if selected:
                document.write(selected); self.scenario_path = Path(selected); self.status_var.set("Scenario saved")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def validate(self) -> None:
        from tkinter import messagebox
        try:
            document = self._get_document()
            report = self.service.validate_document(document)
            self._show(report.to_dict())
            self.status_var.set(f"Validation: {report.status}")
        except Exception as exc:
            messagebox.showerror("Validation failed", str(exc))

    def run(self) -> None:
        from tkinter import messagebox
        try:
            document = self._get_document()
        except Exception as exc:
            messagebox.showerror("Invalid scenario", str(exc)); return
        self.status_var.set("Running…")
        def worker() -> None:
            try:
                result = self.service.run(document=document, run_id="gui-run")
                self.root.after(0, lambda: self._finish_run(document, result))
            except Exception as exc:
                self.root.after(0, lambda: self.status_var.set(f"Run failed: {exc}"))
        threading.Thread(target=worker, daemon=True).start()

    def _finish_run(self, document: GuiScenarioDocument, result: Any) -> None:
        self.last_document = document; self.last_result = result
        self._show(result.to_dict())
        self.status_var.set(f"Run: {result.status}")
        self._draw_result(result.payload)

    def _draw_result(self, payload: dict[str, Any]) -> None:
        self.canvas.delete("all")
        samples = payload.get("samples", [])
        if not samples:
            self.canvas.create_text(12, 18, anchor="w", fill="#d9e4ea", text="No sampled trajectory in this result")
            return
        values = [next(iter(sample.get("positions", {}).values()), 0.0) for sample in samples]
        lo, hi = min(values), max(values)
        span = max(hi - lo, 1e-12)
        width = max(self.canvas.winfo_width(), 200)
        height = 120
        points = []
        for index, value in enumerate(values):
            x = 12 + (width - 24) * index / max(1, len(values) - 1)
            y = 12 + (height - 24) * (1.0 - (value - lo) / span)
            points.extend((x, y))
        self.canvas.create_line(*points, fill="#6ed0c4", width=2, smooth=True)
        self.canvas.create_text(12, 136, anchor="w", fill="#d9e4ea", text=f"first generalized position: {values[0]:.6g} → {values[-1]:.6g}")

    def export_verifier(self) -> None:
        from tkinter import filedialog, messagebox
        try:
            document = self._get_document()
            output = filedialog.askdirectory(title="Export verification bundle")
            if output:
                export_verification_bundle(document=document, output_dir=output)
                self.status_var.set("Verification bundle exported")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))


def launch(*, scenario_path: str | Path | None = None) -> None:
    import tkinter as tk
    root = tk.Tk()
    KinCheckGui(root, scenario_path=scenario_path)
    root.mainloop()


__all__ = ["KinCheckGui", "launch"]
