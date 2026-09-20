# `ContactRegion`

## API 定义

```python
@dataclass(frozen=True)
class ContactRegion:
    occurrence_a: str
    occurrence_b: str
    interface_a: str
    interface_b: str
    lower_m: tuple[float, float, float]
    upper_m: tuple[float, float, float]
    minimum_gap_m: float
    maximum_gap_m: float
    normal_a: tuple[float, float, float]
    purpose: str
    required_connection: bool
```

源码：`src/kincheckapi/physics_geometry.py`。

## 导入

```python
from kincheckapi.dynamics import ContactRegion
```

## 用途

表示 `ContactRegion` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `occurrence_a` | `str` | 必填 | `occurrence_a` 的公开输入或数据字段。 |
| `occurrence_b` | `str` | 必填 | `occurrence_b` 的公开输入或数据字段。 |
| `interface_a` | `str` | 必填 | `interface_a` 的公开输入或数据字段。 |
| `interface_b` | `str` | 必填 | `interface_b` 的公开输入或数据字段。 |
| `lower_m` | `tuple[float, float, float]` | 必填 | `lower_m`，单位 m，必须为有限值。 |
| `upper_m` | `tuple[float, float, float]` | 必填 | `upper_m`，单位 m，必须为有限值。 |
| `minimum_gap_m` | `float` | `0.0` | `minimum_gap_m`，单位 m，必须为有限值。 |
| `maximum_gap_m` | `float` | `0.0002` | `maximum_gap_m`，单位 m，必须为有限值。 |
| `normal_a` | `tuple[float, float, float]` | `(0.0, 0.0, 1.0)` | `normal_a` 的公开输入或数据字段。 |
| `purpose` | `str` | `'ideal mechanical interface'` | `purpose` 的公开输入或数据字段。 |
| `required_connection` | `bool` | `True` | `required_connection` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
