# `export_motion_package`

## API 定义

```python
export_motion_package(*, assembly: AssemblyModel, motion_result: MotionResult, output_path: str | pathlib.Path, asset_root: str | pathlib.Path | None = None, title: str | None = None, require_meshes: bool = False, metadata: Optional[Mapping[str, Any]] = None) -> MotionPackageArtifact
```

源码：`src/kincheckapi/export.py`。

## 导入

```python
from kincheckapi.export import export_motion_package
```

## 用途

把装配、运动结果、校验信息和可选 mesh 写入一个 `.kincheck` 文件。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `output_path` | `str | pathlib.Path` | 必填 | 输出文件路径。 |
| `asset_root` | `str | pathlib.Path | None` | `None` | mesh 等资产允许解析的根目录。 |
| `title` | `str | None` | `None` | `title` 的公开输入或数据字段。 |
| `require_meshes` | `bool` | `False` | `require_meshes` 的公开输入或数据字段。 |
| `metadata` | `Optional[Mapping[str, Any]]` | `None` | 附加的只读结构化元数据。 |

## 返回与失败

返回 `MotionPackageArtifact`。

## 模块约束

- 只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。
- 读取前验证 member path、schema、hash 和跨文件引用。
- `require_meshes=True` 时缺少任何必需 mesh 都应失败。

## 相关文档

- [`结果包`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
