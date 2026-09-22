# `RigidDynamicsScenario`

## API 定义

```python
@dataclass(frozen=True)
class RigidDynamicsScenario:
    states: tuple[kincheckapi.dynamics_v07.GeneralizedJointState, ...]
    mass_matrix: tuple[tuple[float, ...], ...]
    force_vector: tuple[float, ...]
    duration_s: float
    sample_period_s: float
    damping_matrix: tuple[tuple[float, ...], ...] | None
    stiffness_matrix: tuple[tuple[float, ...], ...] | None
    constraints: tuple[kincheckapi.dynamics_v07.ConstraintSpec, ...]
    model_sha256: str | None
    scenario_id: str
    contacts: tuple[Any, ...]
    controllers: tuple[Any, ...]
    brake_policy: Any | None
```

源码：`src/kincheckapi/dynamics_v07.py`。

## 导入

```python
from kincheckapi.dynamics import RigidDynamicsScenario
```

## 用途

表示 `RigidDynamicsScenario` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `states` | `tuple[kincheckapi.dynamics_v07.GeneralizedJointState, ...]` | 必填 | `states` 的公开输入或数据字段。 |
| `mass_matrix` | `tuple[tuple[float, ...], ...]` | 必填 | `mass_matrix` 的公开输入或数据字段。 |
| `force_vector` | `tuple[float, ...]` | 必填 | `force_vector` 的公开输入或数据字段。 |
| `duration_s` | `float` | 必填 | 运行总时长，单位 s，必须为有限正数。 |
| `sample_period_s` | `float` | 必填 | `sample_period_s`，单位 s，必须为有限值。 |
| `damping_matrix` | `tuple[tuple[float, ...], ...] | None` | `None` | `damping_matrix` 的公开输入或数据字段。 |
| `stiffness_matrix` | `tuple[tuple[float, ...], ...] | None` | `None` | `stiffness_matrix` 的公开输入或数据字段。 |
| `constraints` | `tuple[kincheckapi.dynamics_v07.ConstraintSpec, ...]` | `()` | `constraints` 的公开输入或数据字段。 |
| `model_sha256` | `str | None` | `None` | `model_sha256` 的公开输入或数据字段。 |
| `scenario_id` | `str` | `''` | 稳定且可解析的 `scenario_id`。 |
| `contacts` | `tuple[Any, ...]` | `()` | `contacts` 的公开输入或数据字段。 |
| `controllers` | `tuple[Any, ...]` | `()` | `controllers` 的公开输入或数据字段。 |
| `brake_policy` | `Any | None` | `None` | `brake_policy` 的公开输入或数据字段。 |

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
