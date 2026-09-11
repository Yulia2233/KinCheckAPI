# KinCheck Motion Package v1

## 目的

`.kincheck` 是 KinCheckAPI 的后端无关仿真结果包。它用于在 KinCheckAPI 和独立的 KinCheck Viewer App 之间交付同一份装配体运动结果。

文件是一个 ZIP 容器，容器内只允许数据文件和 STL 网格，不允许嵌入 HTML、JavaScript、Python、内置物理后端 模型或其他可执行内容。

## 成员

```text
example.kincheck
├── manifest.json
├── assembly.json
├── motion.json
├── validation.json
└── meshes/*.stl
```

`manifest.json` 是唯一入口，声明格式版本、装配体/工况 ID、单位、成员哈希、Part 到网格的映射和缺失网格列表。

`assembly.json` 使用 `kincheckapi.assembly/1.0` 数据，保存 Part、Component、Connector、Joint、Constraint、Ground 和初始姿态。

`motion.json` 使用 `kincheck.motion/1.0` 数据，保存 `MotionResult` 的关节轨迹、组件/连接点轨迹、残差、限位事件和诊断问题。轨迹位置统一使用米，角度统一使用弧度，时间统一使用秒。

`validation.json` 保存结果状态、问题列表和最大位置/方向残差，方便 Viewer 在不重新求解的情况下显示验证结论。

## 网格规则

- Part 网格以 `meshes/` 下的 STL 保存。
- 相同 SHA256 内容只保存一份，多个 Part 可以引用同一个路径。
- `scale_to_m` 说明 STL 顶点从源 CAD 单位转换到米所需的比例。
- 没有网格的 Part 可以出现在 `missing_mesh_part_ids`；需要完整几何时，导出函数可使用 `require_meshes=True` 拒绝输出。

## 完整性和安全性

读取前必须检查：成员路径是规范化 POSIX 相对路径、没有重复成员、所有成员都被 manifest 索引、大小和 SHA256 匹配、JSON schema 和跨文件 ID 一致。读取器不解压到用户目录，直接从 ZIP 读取校验后的成员。

格式版本由 `schema_version` 管理。Viewer 必须拒绝不支持的主版本，而不是猜测字段含义。

## Python API

```python
from kincheckapi import export

artifact = export.motion_package(
    assembly=assembly,
    motion_result=motion_result,
    output_path="result.kincheck",
    asset_root=cadir_artifact.root,
)

check = export.validate_package(path=artifact.path)
package = export.read_package(path=artifact.path)
mesh_bytes = package.read_mesh(part_id="stage1_planet_gear")
```

`export.motion_package()` 和 `export.export_motion_package()` 是同一个公开导出入口；后者用于表达更明确的函数名。`read_package()` 返回重建后的 `AssemblyModel` 和 `MotionResult`，不会暴露 ZIP、内置物理后端 或 Three.js 内部对象。

## 独立 Viewer

仓库顶层 `viewer/kincheck_viewer.py` 是格式的独立消费者，不属于 `kincheckapi` Python 包。它验证并解包 `.kincheck`，将 `poses` 转换为浏览器播放轨迹，然后从包内 STL 建立 Three.js 场景。整个过程只回放已有结果，不重新运行 内置物理后端 或运动学求解器。
