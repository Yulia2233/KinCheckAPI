# `AssemblyModel`

## API 定义

```python
@dataclass(frozen=True)
class AssemblyModel:
    assembly_id: str
    parts: tuple[Part, ...]
    components: tuple[Component, ...]
    joints: tuple[Joint, ...]
    constraints: tuple[Constraint, ...]
    couplings: tuple[Coupling, ...]
    closures: tuple[Closure, ...]
    grounds: tuple[Ground, ...]
    collision_exclusions: tuple[tuple[str, str], ...]
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import AssemblyModel
```

## 用途

表示 `AssemblyModel` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly_id` | `str` | 必填 | 稳定且可解析的 `assembly_id`。 |
| `parts` | `tuple[Part, ...]` | `()` | `parts` 的公开输入或数据字段。 |
| `components` | `tuple[Component, ...]` | `()` | `components` 的公开输入或数据字段。 |
| `joints` | `tuple[Joint, ...]` | `()` | `joints` 的公开输入或数据字段。 |
| `constraints` | `tuple[Constraint, ...]` | `()` | `constraints` 的公开输入或数据字段。 |
| `couplings` | `tuple[Coupling, ...]` | `()` | `couplings` 的公开输入或数据字段。 |
| `closures` | `tuple[Closure, ...]` | `()` | `closures` 的公开输入或数据字段。 |
| `grounds` | `tuple[Ground, ...]` | `()` | `grounds` 的公开输入或数据字段。 |
| `collision_exclusions` | `tuple[tuple[str, str], ...]` | `()` | `collision_exclusions` 的公开输入或数据字段。 |
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
