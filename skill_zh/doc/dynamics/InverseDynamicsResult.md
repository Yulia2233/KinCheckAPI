# `InverseDynamicsResult`

## API 定义

```python
@dataclass(frozen=True)
class InverseDynamicsResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    request: kincheckapi.dynamic_types.DynamicRequest | None
    generalized_efforts: Mapping[str, float]
    generalized_units: Mapping[str, str]
    joint_powers_w: Mapping[str, float]
    body_wrenches: Mapping[str, Mapping[str, Any]]
```

源码：`src/kincheckapi/dynamic_types.py`。

## 导入

```python
from kincheckapi.dynamics import InverseDynamicsResult
```

## 用途

表示 `InverseDynamicsResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_inverse_dynamics'` | `operation` 的公开输入或数据字段。 |
| `status` | `str` | `'passed'` | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `evidence` | `Mapping[str, Any]` | default_factory | 支持结论的机器可读证据。 |
| `model_sha256` | `str | None` | `None` | `model_sha256` 的公开输入或数据字段。 |
| `result_index` | `int | None` | `None` | `result_index` 的公开输入或数据字段。 |
| `request` | `kincheckapi.dynamic_types.DynamicRequest | None` | `None` | `request` 的公开输入或数据字段。 |
| `generalized_efforts` | `Mapping[str, float]` | default_factory | `generalized_efforts` 的公开输入或数据字段。 |
| `generalized_units` | `Mapping[str, str]` | default_factory | `generalized_units` 的公开输入或数据字段。 |
| `joint_powers_w` | `Mapping[str, float]` | default_factory | `joint_powers_w` 的公开输入或数据字段。 |
| `body_wrenches` | `Mapping[str, Mapping[str, Any]]` | default_factory | `body_wrenches` 的公开输入或数据字段。 |

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
