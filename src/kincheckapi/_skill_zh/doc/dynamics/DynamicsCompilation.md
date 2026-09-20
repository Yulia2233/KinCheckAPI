# `DynamicsCompilation`

## API 定义

```python
@dataclass(frozen=True)
class DynamicsCompilation:
    backend: str
    backend_version: str
    model_xml: str
    body_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    source_sha256: str | None
    _compiled: Any
```

源码：`src/kincheckapi/physics_backend.py`。

## 导入

```python
from kincheckapi.dynamics import DynamicsCompilation
```

## 用途

表示 `DynamicsCompilation` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `backend` | `str` | 必填 | `backend` 的公开输入或数据字段。 |
| `backend_version` | `str` | 必填 | `backend_version` 的公开输入或数据字段。 |
| `model_xml` | `str` | 必填 | `model_xml` 的公开输入或数据字段。 |
| `body_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | 必填 | `body_properties` 的公开输入或数据字段。 |
| `source_sha256` | `str | None` | 必填 | `source_sha256` 的公开输入或数据字段。 |
| `_compiled` | `Any` | 必填 | `_compiled` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
