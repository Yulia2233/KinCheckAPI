# `Coupling`

## API 定义

```python
@dataclass(frozen=True)
class Coupling:
    coupling_id: str
    coupling_type: CouplingType | str
    joint_a_id: str
    joint_b_id: str
    ratio: float
    phase_offset: float
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import Coupling
```

## 用途

表示 `Coupling` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `coupling_id` | `str` | 必填 | 稳定且可解析的 `coupling_id`。 |
| `coupling_type` | `CouplingType | str` | 必填 | `coupling_type` 的公开输入或数据字段。 |
| `joint_a_id` | `str` | 必填 | 稳定且可解析的 `joint_a_id`。 |
| `joint_b_id` | `str` | 必填 | 稳定且可解析的 `joint_b_id`。 |
| `ratio` | `float` | 必填 | `ratio` 的公开输入或数据字段。 |
| `phase_offset` | `float` | `0.0` | `phase_offset` 的公开输入或数据字段。 |
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
