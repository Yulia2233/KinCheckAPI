"""Standalone KinCheck Viewer launcher for ``.kincheck`` motion packages.

This application intentionally lives outside ``src/kincheckapi``. KinCheckAPI
produces the package; this script validates, unpacks, and serves it.
"""

from __future__ import annotations

import argparse
import hashlib
import http.server
import json
from pathlib import Path
import re
import shutil
import webbrowser
from typing import Any, Mapping
import zipfile


PACKAGE_SCHEMA_VERSION = "kincheck.motion-package/1.0"
VIEWER_SCHEMA_VERSION = "kincheck.viewer/1.0"
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


class ViewerPackageError(ValueError):
    """Raised when a .kincheck package cannot be opened by the standalone app."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.") or "part"


def _read_json(archive: zipfile.ZipFile, member: str) -> Mapping[str, Any]:
    try:
        value = json.loads(archive.read(member).decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError) as cause:
        raise ViewerPackageError(f"invalid JSON member: {member}") from cause
    if not isinstance(value, dict):
        raise ViewerPackageError(f"JSON member must be an object: {member}")
    return value


def _verify_package(package_path: Path, archive: zipfile.ZipFile) -> Mapping[str, Any]:
    try:
        manifest = _read_json(archive, "manifest.json")
    except ViewerPackageError:
        raise
    if manifest.get("schema_version") != PACKAGE_SCHEMA_VERSION:
        raise ViewerPackageError(
            f"unsupported package schema: {manifest.get('schema_version')!r}"
        )
    names = {info.filename for info in archive.infolist()}
    for name in names:
        if "\\" in name or name.startswith("/") or ".." in Path(name).parts:
            raise ViewerPackageError(f"unsafe package member path: {name}")
    indexed = manifest.get("files")
    if not isinstance(indexed, list):
        raise ViewerPackageError("manifest.files must be an array")
    for entry in indexed:
        if not isinstance(entry, Mapping):
            raise ViewerPackageError("manifest contains an invalid file index entry")
        member = entry.get("path")
        if not isinstance(member, str) or member not in names:
            raise ViewerPackageError(f"indexed member is missing: {member!r}")
        content = archive.read(member)
        if int(entry.get("bytes", -1)) != len(content):
            raise ViewerPackageError(f"size check failed: {member}")
        if str(entry.get("sha256")) != _sha256(content):
            raise ViewerPackageError(f"hash check failed: {member}")
    required = ("assembly.json", "motion.json", "validation.json")
    missing = [member for member in required if member not in names]
    if missing:
        raise ViewerPackageError(f"required package members are missing: {missing}")
    return manifest


def _material_color(part: Mapping[str, Any] | None, index: int) -> str:
    material = part.get("metadata", {}).get("material") if part else None
    raw = material.get("color") if isinstance(material, Mapping) else None
    if isinstance(raw, (list, tuple)) and len(raw) == 3:
        try:
            channels = [max(0, min(255, round(float(value) * 255))) for value in raw]
        except (TypeError, ValueError):
            channels = []
        if len(channels) == 3 and max(channels) - min(channels) > 25:
            return "#" + "".join(f"{value:02x}" for value in channels)
    return _PALETTE[index % len(_PALETTE)]


def _joint_payload(
    joint_trajectories: Mapping[str, Mapping[str, Any]], joint_id: str | None
) -> Mapping[str, Any] | None:
    if joint_id is None:
        return None
    return joint_trajectories.get(joint_id)


def _joint_unit(joint_type: str | None) -> str:
    if joint_type == "prismatic":
        return "m/s"
    return "rad/s"


def _transmission_display(
    assembly: Mapping[str, Any],
    input_joint_id: str | None,
    output_joint_id: str | None,
) -> tuple[str, str, str, str]:
    joint_types = {
        str(item.get("joint_id")): str(item.get("joint_type"))
        for item in assembly.get("joints", ())
        if isinstance(item, Mapping) and item.get("joint_id")
    }
    input_type = joint_types.get(input_joint_id or "")
    output_type = joint_types.get(output_joint_id or "")
    input_unit = _joint_unit(input_type)
    output_unit = _joint_unit(output_type)
    if input_type == "revolute" and output_type == "prismatic":
        return input_unit, output_unit, "output_over_input", "m/rad"
    if input_type == "prismatic" and output_type == "revolute":
        return input_unit, output_unit, "output_over_input", "rad/m"
    return input_unit, output_unit, "input_over_output", ":1"


def _trajectory_payload(raw: Mapping[str, Any]) -> dict[str, Any]:
    poses = raw.get("poses", ())
    return {
        "component_id": raw.get("component_id"),
        "times_s": [float(value) for value in raw.get("times_s", ())],
        "positions_m": [list(pose["position_m"]) for pose in poses],
        "orientations_xyzw": [list(pose["orientation_xyzw"]) for pose in poses],
    }


def unpack_package(
    *,
    package_path: str | Path,
    output_dir: str | Path,
    input_joint_id: str | None = None,
    output_joint_id: str | None = None,
    expected_ratio: float | None = None,
    title: str | None = None,
) -> Path:
    """Validate a .kincheck package and create a self-contained viewer folder."""

    package = Path(package_path).expanduser().resolve()
    destination = Path(output_dir).expanduser().resolve()
    if not package.is_file():
        raise ViewerPackageError(f"package does not exist: {package}")
    if destination.exists() and not destination.is_dir():
        raise ViewerPackageError(f"output path is not a directory: {destination}")

    with zipfile.ZipFile(package, "r") as archive:
        manifest = _verify_package(package, archive)
        assembly = _read_json(archive, "assembly.json")
        motion_document = _read_json(archive, "motion.json")
        motion = motion_document.get("motion_result")
        if not isinstance(motion, Mapping):
            raise ViewerPackageError("motion.json does not contain motion_result")
        if assembly.get("assembly_id") != manifest.get("assembly_id"):
            raise ViewerPackageError("assembly ID differs from manifest")
        if motion.get("assembly_id") != manifest.get("assembly_id"):
            raise ViewerPackageError("motion assembly ID differs from manifest")
        input_unit, output_unit, ratio_mode, ratio_unit = _transmission_display(
            assembly, input_joint_id, output_joint_id
        )

        destination.mkdir(parents=True, exist_ok=True)
        assets = destination / "assets"
        assets.mkdir(exist_ok=True)
        static_source = Path(__file__).with_name("static")
        if not static_source.is_dir():
            raise ViewerPackageError(f"viewer static resources are missing: {static_source}")
        shutil.copytree(static_source, destination / "static", dirs_exist_ok=True)
        shutil.copy2(static_source / "index.html", destination / "index.html")
        parts = {
            str(item["part_id"]): item
            for item in assembly.get("parts", ())
            if isinstance(item, Mapping) and item.get("part_id")
        }
        mesh_entries = {
            str(item["part_id"]): item
            for item in manifest.get("meshes", ())
            if isinstance(item, Mapping) and item.get("part_id")
        }
        asset_urls: dict[str, str] = {}
        asset_scale_m = 1.0
        for part_id, entry in sorted(mesh_entries.items()):
            member = str(entry.get("path", ""))
            content = archive.read(member)
            filename = f"{_slug(part_id)}-{_sha256(content)[:10]}.stl"
            (assets / filename).write_bytes(content)
            asset_urls[part_id] = f"assets/{filename}"
            asset_scale_m = float(entry.get("scale_to_m", asset_scale_m))

        trajectories = {
            str(item["component_id"]): _trajectory_payload(item)
            for item in motion.get("trajectories", ())
            if isinstance(item, Mapping)
            and item.get("component_id")
            and item.get("connector_id") is None
        }
        ground_ids = {
            str(item["component_id"])
            for item in assembly.get("grounds", ())
            if isinstance(item, Mapping) and item.get("component_id")
        }
        missing_components: list[str] = []
        components: list[dict[str, Any]] = []
        motion_metadata = motion.get("metadata", {})
        workspace = (
            motion_metadata.get("workspace", {})
            if isinstance(motion_metadata, Mapping)
            else {}
        )
        for index, component in enumerate(assembly.get("components", ())):
            if not isinstance(component, Mapping):
                continue
            component_id = str(component["component_id"])
            part_id = str(component["part_id"])
            asset_url = asset_urls.get(part_id)
            if asset_url is None:
                missing_components.append(component_id)
            components.append(
                {
                    "component_id": component_id,
                    "display_name": component.get("display_name") or component_id,
                    "part_id": part_id,
                    "asset_url": asset_url,
                    "color": _material_color(parts.get(part_id), index),
                    "grounded": component_id in ground_ids,
                    "initial_pose": component.get(
                        "initial_pose",
                        {"position_m": [0, 0, 0], "orientation_xyzw": [0, 0, 0, 1]},
                    ),
                    "trajectory": trajectories.get(component_id),
                }
            )

        viewer_manifest = {
            "schema_version": VIEWER_SCHEMA_VERSION,
            "title": title or manifest.get("title") or manifest.get("assembly_id"),
            "assembly_id": manifest.get("assembly_id"),
            "scenario_id": manifest.get("scenario_id"),
            "motion_status": motion.get("status", manifest.get("motion_status")),
            "start_time_s": motion.get("start_time_s", 0.0),
            "end_time_s": motion.get("end_time_s", 0.0),
            "sample_count": len(motion.get("sample_times_s", ())),
            "component_result_scope": motion_metadata.get(
                "component_result_scope", "requested"
            ),
            "backend": {
                "id": motion.get("backend_id", "package"),
                "version": motion.get("backend_version", "1"),
            },
            "asset_length_scale_m": asset_scale_m,
            "components": components,
            "workspace": workspace,
            "metrics": {
                "input": _joint_payload(
                    {str(item["joint_id"]): item for item in motion.get("joint_trajectories", ())},
                    input_joint_id,
                ),
                "output": _joint_payload(
                    {str(item["joint_id"]): item for item in motion.get("joint_trajectories", ())},
                    output_joint_id,
                ),
                "expected_ratio": expected_ratio,
                "input_unit": input_unit,
                "output_unit": output_unit,
                "ratio_mode": ratio_mode,
                "ratio_unit": ratio_unit,
                "maximum_position_residual_m": max(
                    (float(item.get("position_residual_m", 0.0)) for item in motion.get("constraint_residuals", ())),
                    default=0.0,
                ),
                "maximum_orientation_residual_rad": max(
                    (float(item.get("orientation_residual_rad", 0.0)) for item in motion.get("constraint_residuals", ())),
                    default=0.0,
                ),
            },
            "issues": list(motion.get("issues", ())),
            "missing_asset_component_ids": missing_components,
        }
        (destination / "viewer.json").write_text(
            json.dumps(viewer_manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return destination / "index.html"


def serve(*, root: Path, host: str, port: int, open_browser: bool) -> None:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, request, client_address, server):
            super().__init__(request, client_address, server, directory=str(root))

        def log_message(self, format: str, *args: Any) -> None:
            print(f"Viewer HTTP: {format % args}")

    handler = Handler
    server = http.server.ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}/"
    print(f"KinCheck Viewer: {url}")
    print("Press Ctrl-C to stop the viewer.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nViewer stopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Play a KinCheck .kincheck motion package")
    parser.add_argument("package", type=Path, help="path to a .kincheck file")
    parser.add_argument("--output", type=Path, help="viewer directory (default: viewer/runtime/<name>)")
    parser.add_argument("--input-joint", help="joint ID shown as the input speed")
    parser.add_argument("--output-joint", help="joint ID shown as the output speed")
    parser.add_argument("--expected-ratio", type=float)
    parser.add_argument("--title")
    parser.add_argument("--serve", action="store_true", help="start a local web server after unpacking")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--no-open", action="store_true", help="do not open a browser window")
    args = parser.parse_args()
    output = args.output or Path(__file__).with_name("runtime") / args.package.stem
    try:
        index = unpack_package(
            package_path=args.package,
            output_dir=output,
            input_joint_id=args.input_joint,
            output_joint_id=args.output_joint,
            expected_ratio=args.expected_ratio,
            title=args.title,
        )
    except (OSError, zipfile.BadZipFile, ViewerPackageError, KeyError, TypeError, ValueError) as cause:
        parser.error(str(cause))
    print(f"Unpacked viewer: {index}")
    if args.serve:
        serve(root=index.parent, host=args.host, port=args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()
