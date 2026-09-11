# `ViewerArtifact`

## API 定义

```python
@dataclass(frozen=True)
class ViewerArtifact:
    root: pathlib.Path
    index_path: pathlib.Path
    manifest_path: pathlib.Path
    component_count: int
    asset_count: int
    missing_asset_component_ids: tuple[str, ...]
```

源码：`src/kincheckapi/visualization.py`。

## 导入

```python
from kincheckapi.visualization import ViewerArtifact
```

## 用途

表示 `ViewerArtifact` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `root` | `pathlib.Path` | 必填 | `root` 的公开输入或数据字段。 |
| `index_path` | `pathlib.Path` | 必填 | `index_path` 的公开输入或数据字段。 |
| `manifest_path` | `pathlib.Path` | 必填 | `manifest_path` 的公开输入或数据字段。 |
| `component_count` | `int` | 必填 | `component_count` 的公开输入或数据字段。 |
| `asset_count` | `int` | 必填 | `asset_count` 的公开输入或数据字段。 |
| `missing_asset_component_ids` | `tuple[str, ...]` | `()` | 显式指定的 `missing_asset_component_ids` 集合。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 可视化只消费公开 AssemblyModel 和 MotionResult，不读取私有后端状态。
- 导出前检查运动状态、实际轨迹和 mesh 资产。
- viewer 用于复核证据，不替代数值验收检查。

## 相关文档

- [`离线可视化`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
