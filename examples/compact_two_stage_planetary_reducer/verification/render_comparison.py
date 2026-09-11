"""Render the real before/after native trajectories using the four-bar layout."""
from pathlib import Path
import json,tempfile
from zipfile import ZipFile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import vtk
from vtk.util.numpy_support import vtk_to_numpy
CASE_DIR=Path(__file__).resolve().parents[1]
OUTPUT_DIR=CASE_DIR/"output"
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
        assert motion["backend_id"] == "solver"
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
            label = component["component_id"].lower()
            color = (0.62, 0.66, 0.71)
            for token, candidate in (("carrier", (0.22, 0.65, 0.48)), ("sun", (0.92, 0.57, 0.12)), ("planet", (0.25, 0.49, 0.79)), ("shaft", (0.83, 0.37, 0.28))):
                if token in label:
                    color = candidate
                    break
            actor.GetProperty().SetColor(*color)
            grounded = {g["component_id"] for g in assembly["grounds"]}
            if component["component_id"] in grounded or "ring" in label or "housing" in label:
                actor.GetProperty().SetOpacity(0.24)
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


def main():
    width,height=1200,660
    window=vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(width,height)
    window.SetMultiSamples(0)
    renderers=[]
    for side in range(2):
        renderer=vtk.vtkRenderer()
        renderer.SetViewport(side/2,0.16,(side+1)/2,0.82)
        renderer.SetBackground(0.965,0.973,0.982)
        window.AddRenderer(renderer)
        renderers.append(renderer)
    with tempfile.TemporaryDirectory(prefix="reducer-render-") as directory:
        scratch=Path(directory)
        scenes=[]
        reports=[]
        for variant,renderer in zip(("before","after"),renderers):
            (scratch/variant).mkdir()
            scenes.append(load_scene(OUTPUT_DIR/variant/f"{CASE_DIR.name}.kincheck",renderer,scratch/variant))
            reports.append(json.loads((OUTPUT_DIR/variant/f"{CASE_DIR.name}.verification.json").read_text()))
        assert scenes[0][1]==scenes[1][1]
        times=scenes[0][1]
        low,high=np.full(3,np.inf),np.full(3,-np.inf)
        for actors,_ in scenes:
            for actor,matrices,vertices in actors:
                for matrix in matrices:
                    points=vertices @ matrix[:3,:3].T + matrix[:3,3]
                    low=np.minimum(low,points.min(axis=0))
                    high=np.maximum(high,points.max(axis=0))
        center=(low+high)/2
        span=float(max(high-low))
        for renderer in renderers:
            camera=renderer.GetActiveCamera()
            camera.SetFocalPoint(*center)
            camera.SetPosition(*(center+span*np.array([1.2,-2.0,1.5])))
            camera.SetViewUp(0,0,1)
            camera.ParallelProjectionOn()
            camera.SetParallelScale(span*0.67)
            camera.SetClippingRange(span*0.01,span*10)
        capture=vtk.vtkWindowToImageFilter()
        capture.SetInput(window)
        capture.SetInputBufferTypeToRGB()
        capture.ReadFrontBufferOff()
        large,normal,small=font(30),font(20),font(17)
        frames=[]
        for index,time in enumerate(times):
            for actors,_ in scenes:
                set_frame(actors,index)
            window.Render()
            capture.Modified();capture.Update()
            pixels=vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
            frame=Image.fromarray(np.flipud(pixels.reshape(height,width,3)).copy())
            draw=ImageDraw.Draw(frame)
            draw.rectangle((0,0,width,112),fill="white")
            draw.rectangle((0,558,width,height),fill="white")
            draw.line((600,16,600,550),fill="#d8dee8",width=2)
            draw.text((30,18),"修复前",font=large,fill="#a62f32")
            draw.text((630,18),"修复后",font=large,fill="#14765a")
            draw.text((30,63),"传动约束缺失 / 验收失败",font=normal,fill="#46546a")
            draw.text((630,63),f"实测减速比 {reports[1]['measured_ratio']:.6f}:1 / 通过",font=normal,fill="#46546a")
            draw.text((30,574),f"输出速度 {reports[0]['output_speed_rad_s']:.2e} rad/s",font=normal,fill="#a62f32")
            draw.text((630,574),f"输出速度 {reports[1]['output_speed_rad_s']:.6f} rad/s",font=normal,fill="#14765a")
            draw.text((30,622),"真实求解轨迹 / 相同视角与比例 / 外壳半透明 / 4 倍慢放",font=small,fill="#46546a")
            draw.text((985,622),f"t = {time:.2f} s",font=small,fill="#46546a")
            if index==0:
                frame.save(OUTPUT_DIR/"comparison.png")
            frames.append(frame)
        frames[0].save(OUTPUT_DIR/"comparison.gif",save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=False,disposal=2)
    window.Finalize()
    print(OUTPUT_DIR/"comparison.gif",flush=True)
if __name__=="__main__":
    main()
