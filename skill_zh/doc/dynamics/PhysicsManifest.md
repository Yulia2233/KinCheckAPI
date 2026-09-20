# `PhysicsManifest`

## API 定义

```python
@dataclass(frozen=True)
class PhysicsManifest:
    definitions: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    occurrences: tuple[kincheckapi.physics_types.PhysicsOccurrence, ...]
    source_path: str
    source_sha256: str
    producer: Mapping[str, str]
    schema_version: str
    algorithm: str
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import PhysicsManifest
```

## 用途

表示 `PhysicsManifest` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `definitions` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | 必填 | `definitions` 的公开输入或数据字段。 |
| `occurrences` | `tuple[kincheckapi.physics_types.PhysicsOccurrence, ...]` | 必填 | `occurrences` 的公开输入或数据字段。 |
| `source_path` | `str` | 必填 | `source_path` 的公开输入或数据字段。 |
| `source_sha256` | `str` | 必填 | `source_sha256` 的公开输入或数据字段。 |
| `producer` | `Mapping[str, str]` | 必填 | `producer` 的公开输入或数据字段。 |
| `schema_version` | `str` | `'kincheck.physics/1.0'` | `schema_version` 的公开输入或数据字段。 |
| `algorithm` | `str` | `'occt-volume-com-tensor-si/1'` | `algorithm` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
