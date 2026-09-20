# `DynamicsModel`

## API 定义

```python
@dataclass(frozen=True)
class DynamicsModel:
    assembly: AssemblyModel
    component_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    body_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    occurrence_components: Mapping[str, str]
    manifest: kincheckapi.physics_types.PhysicsManifest | None
    payloads: tuple[kincheckapi.physics_types.Payload, ...]
    base_component_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import DynamicsModel
```

## 用途

表示 `DynamicsModel` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `component_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | 必填 | `component_properties` 的公开输入或数据字段。 |
| `body_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | 必填 | `body_properties` 的公开输入或数据字段。 |
| `occurrence_components` | `Mapping[str, str]` | 必填 | `occurrence_components` 的公开输入或数据字段。 |
| `manifest` | `kincheckapi.physics_types.PhysicsManifest | None` | `None` | `manifest` 的公开输入或数据字段。 |
| `payloads` | `tuple[kincheckapi.physics_types.Payload, ...]` | `()` | `payloads` 的公开输入或数据字段。 |
| `base_component_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | default_factory | `base_component_properties` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
