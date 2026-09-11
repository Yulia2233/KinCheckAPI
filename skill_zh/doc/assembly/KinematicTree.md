# `KinematicTree`

## API 定义

```python
@dataclass(frozen=True)
class KinematicTree:
    root_group_ids: tuple[str, ...]
    component_groups: Mapping[str, str]
    group_components: Mapping[str, tuple[str, ...]]
    parent_component_id: Mapping[str, str | None]
    parent_group_id: Mapping[str, str | None]
    depth_by_component_id: Mapping[str, int]
    tree_edges: tuple[KinematicEdge, ...]
    closure_edges: tuple[KinematicEdge, ...]
    disconnected_group_ids: tuple[str, ...]
    grounded_group_ids: tuple[str, ...]
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import KinematicTree
```

## 用途

表示 `KinematicTree` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `root_group_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `root_group_ids` 集合。 |
| `component_groups` | `Mapping[str, str]` | 必填 | `component_groups` 的公开输入或数据字段。 |
| `group_components` | `Mapping[str, tuple[str, ...]]` | 必填 | `group_components` 的公开输入或数据字段。 |
| `parent_component_id` | `Mapping[str, str | None]` | 必填 | 稳定且可解析的 `parent_component_id`。 |
| `parent_group_id` | `Mapping[str, str | None]` | 必填 | 稳定且可解析的 `parent_group_id`。 |
| `depth_by_component_id` | `Mapping[str, int]` | 必填 | 稳定且可解析的 `depth_by_component_id`。 |
| `tree_edges` | `tuple[KinematicEdge, ...]` | 必填 | `tree_edges` 的公开输入或数据字段。 |
| `closure_edges` | `tuple[KinematicEdge, ...]` | 必填 | `closure_edges` 的公开输入或数据字段。 |
| `disconnected_group_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `disconnected_group_ids` 集合。 |
| `grounded_group_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `grounded_group_ids` 集合。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
