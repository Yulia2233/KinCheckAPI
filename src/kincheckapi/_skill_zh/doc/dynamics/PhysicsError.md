# `PhysicsError`

## API 定义

```python
class PhysicsError(KinCheckError): ...

PhysicsError(*, code: 'str', message: 'str | None' = None, report: 'DiagnosticReport | ValidationResult | None' = None, object_ids: 'Sequence[str]' = (), source_paths: 'Sequence[str]' = (), suggested_actions: 'Sequence[str]' = (), details: 'Mapping[str, Any] | None' = None, operation: 'str | None' = None, status: 'str | None' = None, stage: 'str | None' = None) -> 'None'
```

源码：`src/kincheckapi/physics_types.py`。

## 导入

```python
from kincheckapi.dynamics import PhysicsError
```

## 用途

表示 `PhysicsError` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `code` | `str` | 必填 | `code` 的公开输入或数据字段。 |
| `message` | `str | None` | `None` | `message` 的公开输入或数据字段。 |
| `report` | `DiagnosticReport | ValidationResult | None` | `None` | `report` 的公开输入或数据字段。 |
| `object_ids` | `Sequence[str]` | `()` | 显式指定的 `object_ids` 集合。 |
| `source_paths` | `Sequence[str]` | `()` | `source_paths` 的公开输入或数据字段。 |
| `suggested_actions` | `Sequence[str]` | `()` | `suggested_actions` 的公开输入或数据字段。 |
| `details` | `Optional[Mapping[str, Any]]` | `None` | `details` 的公开输入或数据字段。 |
| `operation` | `str | None` | `None` | `operation` 的公开输入或数据字段。 |
| `status` | `str | None` | `None` | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `stage` | `str | None` | `None` | `stage` 的公开输入或数据字段。 |

## 返回与失败

构造公开领域异常。捕获后读取 `code`、`report` 和结构化上下文，不匹配自由文本消息。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应或碰撞冲量。
- 结构、振动和疲劳 API 只对显式线性矩阵、声明材料、应力历程和 S-N 曲线给出可追溯参考结果；自动 BREP 网格、非线性接触、塑性/断裂及非线性振动返回能力边界。

## 相关文档

- [`动力学、结构、振动与疲劳`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
