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
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触容量 API 只检查给定外力；v0.7 刚体接触/冲量 API 必须保留接触状态、动量、能量和收敛证据。
- 结构网格、应力、结构振动和疲劳属于独立 FEACheckAPI；KinCheckAPI 只导出运动、刚体载荷、反力和冲量事实。

## 相关文档

- [`物性、静力与刚体动力学`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
