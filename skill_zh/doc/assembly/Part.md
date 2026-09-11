# `Part`

## API 定义

```python
@dataclass(frozen=True)
class Part:
    part_id: str
    connectors: tuple[Connector, ...]
    asset_paths: Mapping[str, str]
    asset_hashes: Mapping[str, str]
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import Part
```

## 用途

表示 `Part` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `part_id` | `str` | 必填 | 稳定且可解析的 `part_id`。 |
| `connectors` | `tuple[Connector, ...]` | `()` | `connectors` 的公开输入或数据字段。 |
| `asset_paths` | `Mapping[str, str]` | default_factory | `asset_paths` 的公开输入或数据字段。 |
| `asset_hashes` | `Mapping[str, str]` | default_factory | `asset_hashes` 的公开输入或数据字段。 |
| `display_name` | `str | None` | `None` | `display_name` 的公开输入或数据字段。 |
| `source_path` | `str | None` | `None` | `source_path` 的公开输入或数据字段。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
