# `solve_inverse_dynamics`

## API 定义

```python
solve_inverse_dynamics(*, model: kincheckapi.physics_types.DynamicsModel, request: kincheckapi.dynamic_types.DynamicRequest) -> kincheckapi.dynamic_types.InverseDynamicsResult
```

源码：`src/kincheckapi/dynamic_solver.py`。

## 导入

```python
from kincheckapi.dynamics import solve_inverse_dynamics
```

## 用途

求解指定运动学问题：`solve_inverse_dynamics`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | 必填 | `model` 的公开输入或数据字段。 |
| `request` | `kincheckapi.dynamic_types.DynamicRequest` | 必填 | `request` 的公开输入或数据字段。 |

## 返回与失败

返回 `InverseDynamicsResult`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应、碰撞冲量、结构、振动或疲劳结论。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
