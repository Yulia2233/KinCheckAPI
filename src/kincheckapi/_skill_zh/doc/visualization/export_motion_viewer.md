# `export_motion_viewer`

## API 定义

```python
export_motion_viewer(*, assembly: AssemblyModel, motion_result: MotionResult, output_dir: str | pathlib.Path, asset_root: str | pathlib.Path | None = None, title: str | None = None, input_joint_id: str | None = None, output_joint_id: str | None = None, expected_ratio: float | None = None, static_results: tuple[typing.Any, ...] = (), static_checks: tuple[typing.Any, ...] = ()) -> ViewerArtifact
```

源码：`src/kincheckapi/visualization.py`。

## 导入

```python
from kincheckapi.visualization import export_motion_viewer
```

## 用途

导出可离线打开的 Three.js 运动回放资产。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `output_dir` | `str | pathlib.Path` | 必填 | 输出目录。 |
| `asset_root` | `str | pathlib.Path | None` | `None` | mesh 等资产允许解析的根目录。 |
| `title` | `str | None` | `None` | `title` 的公开输入或数据字段。 |
| `input_joint_id` | `str | None` | `None` | 稳定且可解析的 `input_joint_id`。 |
| `output_joint_id` | `str | None` | `None` | 稳定且可解析的 `output_joint_id`。 |
| `expected_ratio` | `float | None` | `None` | 期望传动比的正幅值；方向由 `expected_direction` 单独表达。 |
| `static_results` | `tuple[Any, ...]` | `()` | `static_results` 的公开输入或数据字段。 |
| `static_checks` | `tuple[Any, ...]` | `()` | `static_checks` 的公开输入或数据字段。 |

## 返回与失败

返回 `ViewerArtifact`。

## 模块约束

- 可视化只消费公开 AssemblyModel 和 MotionResult，不读取私有后端状态。
- 导出前检查运动状态、实际轨迹和 mesh 资产。
- viewer 用于复核证据，不替代数值验收检查。

## 相关文档

- [`离线可视化`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
