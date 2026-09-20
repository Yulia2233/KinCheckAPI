# `build_dynamics_model`

## API 定义

```python
build_dynamics_model(*, assembly: AssemblyModel, manifest: kincheckapi.physics_types.PhysicsManifest | None = None, component_properties: Optional[Mapping[str, kincheckapi.physics_types.RigidBodyProperties]] = None, occurrence_components: Optional[Mapping[str, str]] = None, payloads: Sequence[kincheckapi.physics_types.Payload] = ()) -> kincheckapi.physics_types.DynamicsModel
```

源码：`src/kincheckapi/physics_mass.py`。

## 导入

```python
from kincheckapi.dynamics import build_dynamics_model
```

## 用途

执行公开操作 `build_dynamics_model`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `manifest` | `kincheckapi.physics_types.PhysicsManifest | None` | `None` | `manifest` 的公开输入或数据字段。 |
| `component_properties` | `Optional[Mapping[str, kincheckapi.physics_types.RigidBodyProperties]]` | `None` | `component_properties` 的公开输入或数据字段。 |
| `occurrence_components` | `Optional[Mapping[str, str]]` | `None` | `occurrence_components` 的公开输入或数据字段。 |
| `payloads` | `Sequence[kincheckapi.physics_types.Payload]` | `()` | `payloads` 的公开输入或数据字段。 |

## 返回与失败

返回 `DynamicsModel`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
