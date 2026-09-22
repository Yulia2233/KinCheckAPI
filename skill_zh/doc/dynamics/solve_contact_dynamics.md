# `solve_contact_dynamics`

## API 定义

```python
solve_contact_dynamics(*, interface: kincheckapi.dynamics_v07.ContactInterface, times_s: Sequence[float], relative_gap_m: Sequence[float], relative_normal_velocity_m_s: Sequence[float], relative_tangential_velocity_m_s: Optional[Sequence[Sequence[float]]] = None) -> kincheckapi.dynamics_v07.ContactDynamicsResult
```

源码：`src/kincheckapi/dynamics_v07.py`。

## 导入

```python
from kincheckapi.dynamics import solve_contact_dynamics
```

## 用途

求解指定运动学问题：`solve_contact_dynamics`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `interface` | `kincheckapi.dynamics_v07.ContactInterface` | 必填 | `interface` 的公开输入或数据字段。 |
| `times_s` | `Sequence[float]` | 必填 | `times_s`，单位 s，必须为有限值。 |
| `relative_gap_m` | `Sequence[float]` | 必填 | `relative_gap_m`，单位 m，必须为有限值。 |
| `relative_normal_velocity_m_s` | `Sequence[float]` | 必填 | `relative_normal_velocity_m_s`，单位 m/s，必须为有限值。 |
| `relative_tangential_velocity_m_s` | `Optional[Sequence[Sequence[float]]]` | `None` | `relative_tangential_velocity_m_s`，单位 m/s，必须为有限值。 |

## 返回与失败

返回 `ContactDynamicsResult`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触容量 API 只检查给定外力；v0.7 刚体接触/冲量 API 必须保留接触状态、动量、能量和收敛证据。
- 结构网格、应力、结构振动和疲劳属于独立 FEACheckAPI；KinCheckAPI 只导出运动、刚体载荷、反力和冲量事实。

## 相关文档

- [`物性、静力与刚体动力学`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
