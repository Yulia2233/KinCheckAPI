# `TransientResult`

## API 定义

```python
@dataclass(frozen=True)
class TransientResult:
    operation: str
    status: str
    issues: tuple[SimIssue, ...]
    evidence: Mapping[str, Any]
    model_sha256: str | None
    result_index: int | None
    times_s: tuple[float, ...]
    displacement_m: tuple[tuple[float, ...], ...]
    velocity_m_s: tuple[tuple[float, ...], ...]
    acceleration_m_s2: tuple[tuple[float, ...], ...]
    time_step_s: float
```

源码：`src/kincheckapi/vibration.py`。

## 导入

```python
from kincheckapi.dynamics import TransientResult
```

## 用途

表示 `TransientResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `operation` | `str` | `'solve_transient_response'` | `operation` 的公开输入或数据字段。 |
| `status` | `str` | `'passed'` | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `evidence` | `Mapping[str, Any]` | default_factory | 支持结论的机器可读证据。 |
| `model_sha256` | `str | None` | `None` | `model_sha256` 的公开输入或数据字段。 |
| `result_index` | `int | None` | `None` | `result_index` 的公开输入或数据字段。 |
| `times_s` | `tuple[float, ...]` | `()` | `times_s`，单位 s，必须为有限值。 |
| `displacement_m` | `tuple[tuple[float, ...], ...]` | `()` | `displacement_m`，单位 m，必须为有限值。 |
| `velocity_m_s` | `tuple[tuple[float, ...], ...]` | `()` | `velocity_m_s`，单位 m/s，必须为有限值。 |
| `acceleration_m_s2` | `tuple[tuple[float, ...], ...]` | `()` | `acceleration_m_s2`，单位 m/s^2，必须为有限值。 |
| `time_step_s` | `float` | `0.0` | `time_step_s`，单位 s，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应或碰撞冲量。
- 结构、振动和疲劳 API 只对显式线性矩阵、声明材料、应力历程和 S-N 曲线给出可追溯参考结果；自动 BREP 网格、非线性接触、塑性/断裂及非线性振动返回能力边界。

## 相关文档

- [`动力学、结构、振动与疲劳`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
