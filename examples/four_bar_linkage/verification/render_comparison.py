"""Render the two actual mesh packages on the same reference motion as a GIF.

Requires VTK, NumPy, and Pillow. Run the two simulation scripts first.
The animation is a geometry comparison, not a native solver accuracy claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import vtk
from vtk.util.numpy_support import vtk_to_numpy


CASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = CASE_DIR / "output"
ROOT_ID = "node/four_bar_linkage"
COLORS = {
    ROOT_ID: (0.48, 0.53, 0.60),
    f"{ROOT_ID}/crank": (0.90, 0.56, 0.16),
    f"{ROOT_ID}/coupler": (0.20, 0.49, 0.77),
    f"{ROOT_ID}/rocker": (0.25, 0.64, 0.49),
}


def pose_matrix(pose):
    x, y, z, w = pose["orientation_xyzw"]
    matrix = np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w), 0],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w), 0],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y), 0],
        [0, 0, 0, 1],
    ], dtype=float)
    matrix[:3, 3] = pose["position_m"]
    return matrix


def load_scene(package_path, renderer, scratch):
    with ZipFile(package_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assembly = json.loads(archive.read("assembly.json"))
        motion = json.loads(archive.read("motion.json"))["motion_result"]
        assert motion["backend_id"] == "closed-form-kinematics"
        mesh_paths = {item["part_id"]: item["path"] for item in manifest["meshes"]}
        trajectories = {item["component_id"]: item["poses"] for item in motion["trajectories"]}
        actors = []
        for index, component in enumerate(assembly["components"]):
            mesh_path = scratch / f"{index}.stl"
            mesh_path.write_bytes(archive.read(mesh_paths[component["part_id"]]))
            reader = vtk.vtkSTLReader()
            reader.SetFileName(str(mesh_path))
            reader.Update()
            normals = vtk.vtkPolyDataNormals()
            normals.SetInputConnection(reader.GetOutputPort())
            normals.SetFeatureAngle(45)
            normals.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(normals.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*COLORS[component["component_id"]])
            actor.GetProperty().SetAmbient(0.22)
            actor.GetProperty().SetDiffuse(0.72)
            actor.GetProperty().SetSpecular(0.30)
            actor.GetProperty().SetSpecularPower(28)
            renderer.AddActor(actor)
            vertices = vtk_to_numpy(reader.GetOutput().GetPoints().GetData()).copy()
            matrices = [pose_matrix(pose) for pose in trajectories[component["component_id"]]]
            actors.append((actor, matrices, vertices))
        return actors, motion["sample_times_s"]


def set_frame(actors, index):
    for actor, matrices, _vertices in actors:
        transform = vtk.vtkMatrix4x4()
        transform.DeepCopy(matrices[index].ravel())
        actor.SetUserMatrix(transform)


def font(size):
    candidates = (
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    )
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError("Install a CJK font or update font() for this platform.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Render one frame before the full GIF.")
    args = parser.parse_args()
    width, height = 1200, 660
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(width, height)
    window.SetMultiSamples(8)
    renderers = []
    for side in range(2):
        renderer = vtk.vtkRenderer()
        renderer.SetViewport(side / 2, 0.13, (side + 1) / 2, 0.83)
        renderer.SetBackground(0.965, 0.973, 0.982)
        window.AddRenderer(renderer)
        renderers.append(renderer)
    with tempfile.TemporaryDirectory(prefix="four-bar-render-") as directory:
        scratch = Path(directory)
        scenes = []
        for variant, renderer, name in (
            ("before", renderers[0], "four_bar_linkage_before_optimization.kincheck"),
            ("after", renderers[1], "four_bar_linkage_full_cycle.kincheck"),
        ):
            (scratch / variant).mkdir()
            scenes.append(load_scene(OUTPUT_DIR / variant / name, renderer, scratch / variant))
        assert scenes[0][1] == scenes[1][1], "Both variants must use identical reference timestamps."
        times = scenes[0][1]
        indices = list(range(0, len(times) - 1, 3))
        low, high = np.full(3, np.inf), np.full(3, -np.inf)
        for actors, _times in scenes:
            for _actor, matrices, vertices in actors:
                for index in indices:
                    matrix = matrices[index]
                    points = np.einsum("ij,kj->ki", matrix[:3, :3], vertices, optimize=False) + matrix[:3, 3]
                    if not np.isfinite(points).all():
                        raise ValueError("Non-finite transformed mesh coordinates")
                    low = np.minimum(low, points.min(axis=0))
                    high = np.maximum(high, points.max(axis=0))
        center = (low + high) / 2
        for renderer in renderers:
            camera = renderer.GetActiveCamera()
            camera.SetFocalPoint(*center)
            camera.SetPosition(*(center + np.array([0.08, -0.18, 0.18])))
            camera.SetViewUp(0, 0, 1)
            camera.ParallelProjectionOn()
            camera.SetParallelScale(float(max(high - low) * 0.47))
            camera.SetClippingRange(0.001, 1.0)
        capture = vtk.vtkWindowToImageFilter()
        capture.SetInput(window)
        capture.SetInputBufferTypeToRGB()
        capture.ReadFrontBufferOff()
        title_font, text_font, small_font = font(30), font(20), font(17)
        before = json.loads((OUTPUT_DIR / "before/four_bar_linkage.before_optimization.json").read_text())
        after = json.loads((OUTPUT_DIR / "after/four_bar_linkage.optimization.json").read_text())
        count_before = before["clearance"]["event_count"]
        count_after = after["clearance_after_model_optimization"]["event_count"]
        assert count_before > 0 and count_after == 0
        frames = []
        for number, index in enumerate(indices[:1] if args.preview else indices):
            for actors, _times in scenes:
                set_frame(actors, index)
            window.Render()
            capture.Modified()
            capture.Update()
            pixels = vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
            frame = Image.fromarray(np.flipud(pixels.reshape(height, width, 3)).copy())
            draw = ImageDraw.Draw(frame)
            draw.rectangle((0, 0, width, 112), fill="#ffffff")
            draw.rectangle((0, 570, width, height), fill="#ffffff")
            draw.line((600, 25, 600, 555), fill="#d8dee8", width=2)
            draw.text((30, 18), "优化前", font=title_font, fill="#a62f32")
            draw.text((630, 18), "优化后", font=title_font, fill="#14765a")
            draw.text((30, 63), "同层布置 · 原销轴", font=text_font, fill="#46546a")
            draw.text((630, 63), "轴向错层 · 调整销轴", font=text_font, fill="#46546a")
            draw.text((30, 582), f"301 帧检查：{count_before} 个干涉事件", font=text_font, fill="#a62f32")
            draw.text((630, 582), f"301 帧检查：{count_after} 个干涉事件", font=text_font, fill="#14765a")
            draw.text((30, 624), "实际模型网格 / 同一闭式参考轨迹 / 相同视角与比例", font=small_font, fill="#46546a")
            draw.text((950, 624), f"t = {times[index]:4.1f} / 10.0 s", font=small_font, fill="#46546a")
            if number == 0:
                frame.save(OUTPUT_DIR / "comparison.png")
            frames.append(frame)
            if number % 20 == 0:
                print(f"Rendered {number + 1}/{1 if args.preview else len(indices)} frames", flush=True)
        if not args.preview:
            frames[0].save(
                OUTPUT_DIR / "comparison.gif", save_all=True, append_images=frames[1:],
                duration=100, loop=0, optimize=False, disposal=2,
            )
            print(f"GIF: {OUTPUT_DIR / 'comparison.gif'}", flush=True)
    window.Finalize()


if __name__ == "__main__":
    main()
