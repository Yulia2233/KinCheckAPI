# `SupportSpec`

## API 定义

```python
@dataclass(frozen=True)
class SupportSpec:
    support_id: str
    component_id: str
    occurrence_id: str
    interface_name: str
    kind: str
    frame_id: str
    point_m: tuple[float, float, float]
    normal: tuple[float, float, float]
    evidence_source: str | None
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import SupportSpec
```

## 用途

表示 `SupportSpec` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `support_id` | `str` | 必填 | 稳定且可解析的 `support_id`。 |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `occurrence_id` | `str` | 必填 | 稳定且可解析的 `occurrence_id`。 |
| `interface_name` | `str` | 必填 | `interface_name` 的公开输入或数据字段。 |
| `kind` | `str` | `'fixed'` | `kind` 的公开输入或数据字段。 |
| `frame_id` | `str` | `'world'` | 稳定且可解析的 `frame_id`。 |
| `point_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `point_m`，单位 m，必须为有限值。 |
| `normal` | `tuple[float, float, float]` | `(0.0, 0.0, 1.0)` | `normal` 的公开输入或数据字段。 |
| `evidence_source` | `str | None` | `None` | `evidence_source` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
