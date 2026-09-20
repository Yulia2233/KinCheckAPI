# `StaticRequest`

## API 定义

```python
@dataclass(frozen=True)
class StaticRequest:
    gravity: kincheckapi.physics_types.GravityField
    supports: tuple[kincheckapi.physics_types.SupportSpec, ...]
    joint_positions: Mapping[str, float]
    joint_modes: Mapping[str, str]
    loads: tuple[kincheckapi.physics_types.WrenchLoad, ...]
    request_individual_support_reactions: bool
    force_tolerance_n: float
    moment_tolerance_nm: float
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import StaticRequest
```

## 用途

表示 `StaticRequest` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `gravity` | `kincheckapi.physics_types.GravityField` | 必填 | `gravity` 的公开输入或数据字段。 |
| `supports` | `tuple[kincheckapi.physics_types.SupportSpec, ...]` | 必填 | `supports` 的公开输入或数据字段。 |
| `joint_positions` | `Mapping[str, float]` | 必填 | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |
| `joint_modes` | `Mapping[str, str]` | 必填 | `joint_modes` 的公开输入或数据字段。 |
| `loads` | `tuple[kincheckapi.physics_types.WrenchLoad, ...]` | `()` | `loads` 的公开输入或数据字段。 |
| `request_individual_support_reactions` | `bool` | `False` | `request_individual_support_reactions` 的公开输入或数据字段。 |
| `force_tolerance_n` | `float` | `0.01` | `force_tolerance_n` 的公开输入或数据字段。 |
| `moment_tolerance_nm` | `float` | `0.001` | `moment_tolerance_nm` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
