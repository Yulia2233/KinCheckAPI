"""Export deterministic, browser-based motion playback artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Mapping

from .assembly import AssemblyModel, Part, Pose
from .errors import VisualizationExportError
from .result import JointTrajectory, MotionResult, Trajectory


VIEWER_SCHEMA_VERSION = "kincheck.viewer/1.0"
_STATIC_DIR = Path(__file__).with_name("_viewer_static")
_LENGTH_SCALES_M = {"m": 1.0, "mm": 1e-3, "cm": 1e-2}
_PALETTE = (
    "#3f7d9b",
    "#d88c3a",
    "#4f8a65",
    "#a95d68",
    "#7667a8",
    "#b5a13a",
    "#347f7a",
    "#7b6b5a",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerArtifact:
    root: Path
    index_path: Path
    manifest_path: Path
    component_count: int
    asset_count: int
    missing_asset_component_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "index_path": str(self.index_path),
            "manifest_path": str(self.manifest_path),
            "component_count": self.component_count,
            "asset_count": self.asset_count,
            "missing_asset_component_ids": list(self.missing_asset_component_ids),
        }


def _fail(
    *,
    code: str,
    message: str,
    object_ids: tuple[str, ...] = (),
    paths: tuple[str, ...] = (),
) -> None:
    raise VisualizationExportError(
        code=code,
        message=message,
        object_ids=object_ids,
        source_paths=paths,
        suggested_actions=(
            "Provide matching public AssemblyModel and MotionResult data, then retry.",
        ),
    )


def _pose_payload(pose: Pose) -> dict[str, list[float]]:
    return {
        "position_m": [float(value) for value in pose.position_m],
        "orientation_xyzw": [float(value) for value in pose.orientation_xyzw],
    }


def _trajectory_payload(trajectory: Trajectory) -> dict[str, Any]:
    return {
        "times_s": [float(value) for value in trajectory.times_s],
        "positions_m": [
            [float(value) for value in pose.position_m] for pose in trajectory.poses
        ],
        "orientations_xyzw": [
            [float(value) for value in pose.orientation_xyzw]
            for pose in trajectory.poses
        ],
    }


def _joint_payload(trajectory: JointTrajectory | None) -> dict[str, Any] | None:
    if trajectory is None:
        return None
    return {
        "joint_id": trajectory.joint_id,
        "times_s": [float(value) for value in trajectory.times_s],
        "positions": [float(value) for value in trajectory.positions],
        "velocities": [float(value) for value in trajectory.velocities],
        "accelerations": [float(value) for value in trajectory.accelerations],
    }


def _resolve_asset(*, part: Part, asset_root: Path | None) -> Path | None:
    raw_stl = part.asset_paths.get("stl")
    if raw_stl:
        candidate = Path(raw_stl).expanduser()
        if not candidate.is_absolute() and asset_root is not None:
            candidate = asset_root / candidate
        if candidate.is_file():
            return candidate.resolve()

    if asset_root is None:
        return None
    candidates = [asset_root / "parts" / f"{part.part_id}.stl"]
    if part.source_path and part.source_path.endswith(".part.json"):
        candidates.append(
            asset_root / f"{part.source_path.removesuffix('.part.json')}.stl"
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _safe_asset_name(*, part_id: str, source: Path) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", part_id).strip("-.") or "part"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:10]
    return f"{slug}-{digest}.stl"


def _material_color(*, part: Part, index: int) -> str:
    material = part.metadata.get("material")
    if isinstance(material, Mapping):
        raw = material.get("color")
        if isinstance(raw, (tuple, list)) and len(raw) == 3:
            try:
                channels = tuple(
                    max(0, min(255, round(float(value) * 255))) for value in raw
                )
            except (TypeError, ValueError):
                channels = ()
            if len(channels) == 3:
                # Preserve source material intent, with a small deterministic tint
                # so repeated steel parts remain distinguishable in motion.
                base = _PALETTE[index % len(_PALETTE)]
                if max(channels) - min(channels) > 25:
                    return "#" + "".join(f"{value:02x}" for value in channels)
                return base
    return _PALETTE[index % len(_PALETTE)]


def export_motion_viewer(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    output_dir: str | Path,
    asset_root: str | Path | None = None,
    title: str | None = None,
    input_joint_id: str | None = None,
    output_joint_id: str | None = None,
    expected_ratio: float | None = None,
    static_results: tuple[Any, ...] = (),
    static_checks: tuple[Any, ...] = (),
) -> ViewerArtifact:
    """Export a Three.js motion viewer without exposing backend-native objects."""

    if not isinstance(assembly, AssemblyModel):
        _fail(
            code="KINCHECK-VIEWER-ASSEMBLY-INVALID",
            message="assembly must be an AssemblyModel",
        )
    if not isinstance(motion_result, MotionResult):
        _fail(
            code="KINCHECK-VIEWER-MOTION-INVALID",
            message="motion_result must be a MotionResult",
        )
    if motion_result.assembly_id != assembly.assembly_id:
        _fail(
            code="KINCHECK-VIEWER-ASSEMBLY-MISMATCH",
            message="MotionResult assembly_id does not match the AssemblyModel.",
            object_ids=(assembly.assembly_id, motion_result.assembly_id),
        )

    destination = Path(output_dir).expanduser().resolve()
    if destination.exists() and not destination.is_dir():
        _fail(
            code="KINCHECK-VIEWER-OUTPUT-INVALID",
            message="Viewer output path exists and is not a directory.",
            paths=(str(destination),),
        )
    destination.mkdir(parents=True, exist_ok=True)
    assets_dir = destination / "assets"
    assets_dir.mkdir(exist_ok=True)

    root = Path(asset_root).expanduser().resolve() if asset_root is not None else None
    if root is not None and not root.is_dir():
        _fail(
            code="KINCHECK-VIEWER-ASSET-ROOT-INVALID",
            message="asset_root must be an existing MJCF asset directory.",
            paths=(str(root),),
        )

    component_trajectories = {
        item.component_id: item
        for item in motion_result.trajectories
        if item.connector_id is None
    }
    parts = {part.part_id: part for part in assembly.parts}
    grounds = {item.component_id for item in assembly.grounds}
    copied_assets: dict[Path, str] = {}
    missing: list[str] = []
    components: list[dict[str, Any]] = []

    for index, component in enumerate(assembly.components):
        part = parts.get(component.part_id)
        source = (
            _resolve_asset(part=part, asset_root=root) if part is not None else None
        )
        asset_url: str | None = None
        if source is not None:
            asset_url = copied_assets.get(source)
            if asset_url is None:
                target = assets_dir / _safe_asset_name(
                    part_id=component.part_id, source=source
                )
                shutil.copy2(source, target)
                asset_url = f"assets/{target.name}"
                copied_assets[source] = asset_url
        else:
            missing.append(component.component_id)

        trajectory = component_trajectories.get(component.component_id)
        components.append(
            {
                "component_id": component.component_id,
                "display_name": component.display_name or component.component_id,
                "part_id": component.part_id,
                "asset_url": asset_url,
                "color": _material_color(part=part, index=index)
                if part is not None
                else _PALETTE[index % len(_PALETTE)],
                "grounded": component.component_id in grounds,
                "initial_pose": _pose_payload(component.initial_pose),
                "trajectory": _trajectory_payload(trajectory)
                if trajectory is not None
                else None,
            }
        )

    units = assembly.metadata.get("units", {})
    length_unit = units.get("length", "m") if isinstance(units, Mapping) else "m"
    asset_scale_m = _LENGTH_SCALES_M.get(str(length_unit), 1.0)
    input_trajectory = (
        motion_result.get_joint_trajectory(joint_id=input_joint_id)
        if input_joint_id
        else None
    )
    output_trajectory = (
        motion_result.get_joint_trajectory(joint_id=output_joint_id)
        if output_joint_id
        else None
    )
    if input_joint_id and input_trajectory is None:
        _fail(
            code="KINCHECK-VIEWER-JOINT-NOT-FOUND",
            message="Input Joint trajectory is not present in MotionResult.",
            object_ids=(input_joint_id,),
        )
    if output_joint_id and output_trajectory is None:
        _fail(
            code="KINCHECK-VIEWER-JOINT-NOT-FOUND",
            message="Output Joint trajectory is not present in MotionResult.",
            object_ids=(output_joint_id,),
        )

    input_joint = (
        assembly.get_joint(joint_id=input_joint_id) if input_joint_id else None
    )
    output_joint = (
        assembly.get_joint(joint_id=output_joint_id) if output_joint_id else None
    )
    input_type = input_joint.joint_type.value if input_joint else None
    output_type = output_joint.joint_type.value if output_joint else None
    input_unit = "m/s" if input_type == "prismatic" else "rad/s"
    output_unit = "m/s" if output_type == "prismatic" else "rad/s"
    ratio_mode, ratio_unit = "input_over_output", ":1"
    if (input_type, output_type) == ("revolute", "prismatic"):
        ratio_mode, ratio_unit = "output_over_input", "m/rad"
    elif (input_type, output_type) == ("prismatic", "revolute"):
        ratio_mode, ratio_unit = "output_over_input", "rad/m"
    manifest = {
        "schema_version": VIEWER_SCHEMA_VERSION,
        "physics": {
            "static_results": [r.to_dict() for r in static_results],
            "checks": [r.to_dict() for r in static_checks],
            "acceptance_passed": all(r.passed for r in static_results)
            and all(r.passed for r in static_checks),
        }
        if static_results
        else None,
        "title": title or assembly.display_name or assembly.assembly_id,
        "assembly_id": assembly.assembly_id,
        "scenario_id": motion_result.scenario_id,
        "motion_status": motion_result.status,
        "start_time_s": motion_result.start_time_s,
        "end_time_s": motion_result.end_time_s,
        "sample_count": len(motion_result.sample_times_s),
        "physics_case_count": len(static_results),
        "component_result_scope": motion_result.metadata.get(
            "component_result_scope", "requested"
        ),
        "backend": {
            "id": motion_result.backend_id,
            "version": motion_result.backend_version,
        },
        "asset_length_scale_m": asset_scale_m,
        "components": components,
        "workspace": motion_result.to_dict()["metadata"].get("workspace", {}),
        "metrics": {
            "input": _joint_payload(input_trajectory),
            "output": _joint_payload(output_trajectory),
            "expected_ratio": float(expected_ratio)
            if expected_ratio is not None
            else None,
            "input_unit": input_unit,
            "output_unit": output_unit,
            "ratio_mode": ratio_mode,
            "ratio_unit": ratio_unit,
            "maximum_position_residual_m": max(
                (
                    item.position_residual_m
                    for item in motion_result.constraint_residuals
                ),
                default=0.0,
            ),
            "maximum_orientation_residual_rad": max(
                (
                    item.orientation_residual_rad
                    for item in motion_result.constraint_residuals
                ),
                default=0.0,
            ),
        },
        "issues": [item.to_dict() for item in motion_result.issues],
        "missing_asset_component_ids": missing,
    }
    manifest_path = destination / "viewer.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not _STATIC_DIR.is_dir():
        _fail(
            code="KINCHECK-VIEWER-STATIC-MISSING",
            message="Packaged viewer resources are missing.",
            paths=(str(_STATIC_DIR),),
        )
    shutil.copytree(_STATIC_DIR, destination / "static", dirs_exist_ok=True)
    index_path = destination / "index.html"
    shutil.copy2(_STATIC_DIR / "index.html", index_path)

    return ViewerArtifact(
        root=destination,
        index_path=index_path,
        manifest_path=manifest_path,
        component_count=len(components),
        asset_count=len(copied_assets),
        missing_asset_component_ids=tuple(missing),
    )


__all__ = [
    "VIEWER_SCHEMA_VERSION",
    "ViewerArtifact",
    "export_motion_viewer",
]
