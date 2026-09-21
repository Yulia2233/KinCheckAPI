# `Payload`

## API 定义

```python
@dataclass(frozen=True)
class Payload:
    payload_id: str
    component_id: str
    cad_occurrence_id: str | None
    properties: kincheckapi.physics_types.RigidBodyProperties | None
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import Payload
```

## 用途

表示 `Payload` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `payload_id` | `str` | 必填 | 稳定且可解析的 `payload_id`。 |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `cad_occurrence_id` | `str | None` | `None` | 稳定且可解析的 `cad_occurrence_id`。 |
| `properties` | `kincheckapi.physics_types.RigidBodyProperties | None` | `None` | `properties` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应、碰撞冲量、结构、振动或疲劳结论。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
