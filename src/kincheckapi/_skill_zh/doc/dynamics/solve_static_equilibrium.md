# `solve_static_equilibrium`

## API 定义

```python
solve_static_equilibrium(*, model: kincheckapi.physics_types.DynamicsModel, request: kincheckapi.physics_types.StaticRequest) -> kincheckapi.physics_types.StaticResult
```

源码：`src/kincheckapi/statics.py`。

## 导入

```python
from kincheckapi.dynamics import solve_static_equilibrium
```

## 用途

求解指定运动学问题：`solve_static_equilibrium`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | 必填 | `model` 的公开输入或数据字段。 |
| `request` | `kincheckapi.physics_types.StaticRequest` | 必填 | `request` 的公开输入或数据字段。 |

## 返回与失败

返回 `StaticResult`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
