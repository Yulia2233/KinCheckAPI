# `MotionPackageArtifact`

## API 定义

```python
@dataclass(frozen=True)
class MotionPackageArtifact:
    path: pathlib.Path
    sha256: str
    bytes: int
    schema_version: str
    component_count: int
    trajectory_count: int
    mesh_count: int
    missing_mesh_part_ids: tuple[str, ...]
```

源码：`src/kincheckapi/export.py`。

## 导入

```python
from kincheckapi.export import MotionPackageArtifact
```

## 用途

表示 `MotionPackageArtifact` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `path` | `pathlib.Path` | 必填 | 输入或输出文件路径；具体方向见用途说明。 |
| `sha256` | `str` | 必填 | `sha256` 的公开输入或数据字段。 |
| `bytes` | `int` | 必填 | `bytes` 的公开输入或数据字段。 |
| `schema_version` | `str` | 必填 | `schema_version` 的公开输入或数据字段。 |
| `component_count` | `int` | 必填 | `component_count` 的公开输入或数据字段。 |
| `trajectory_count` | `int` | 必填 | `trajectory_count` 的公开输入或数据字段。 |
| `mesh_count` | `int` | 必填 | `mesh_count` 的公开输入或数据字段。 |
| `missing_mesh_part_ids` | `tuple[str, ...]` | `()` | 显式指定的 `missing_mesh_part_ids` 集合。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。
- 读取前验证 member path、schema、hash 和跨文件引用。
- `require_meshes=True` 时缺少任何必需 mesh 都应失败。

## 相关文档

- [`结果包`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
