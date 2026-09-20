# `PhysicsOccurrence`

## API 定义

```python
@dataclass(frozen=True)
class PhysicsOccurrence:
    occurrence_id: str
    definition_id: str
    revision: str
    content_hash: str
    pose_world: Pose
    properties: kincheckapi.physics_types.RigidBodyProperties
    interfaces: Mapping[str, Any]
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import PhysicsOccurrence
```

## 用途

表示 `PhysicsOccurrence` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `occurrence_id` | `str` | 必填 | 稳定且可解析的 `occurrence_id`。 |
| `definition_id` | `str` | 必填 | 稳定且可解析的 `definition_id`。 |
| `revision` | `str` | 必填 | `revision` 的公开输入或数据字段。 |
| `content_hash` | `str` | 必填 | `content_hash` 的公开输入或数据字段。 |
| `pose_world` | `Pose` | 必填 | `pose_world` 的公开输入或数据字段。 |
| `properties` | `kincheckapi.physics_types.RigidBodyProperties` | 必填 | `properties` 的公开输入或数据字段。 |
| `interfaces` | `Mapping[str, Any]` | default_factory | `interfaces` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
