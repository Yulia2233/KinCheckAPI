# `check_resonance_margin`

## API 定义

```python
check_resonance_margin(*, natural_frequencies_hz: Sequence[float], excitation_frequencies_hz: Sequence[float], minimum_margin_hz: float, damping_ratio: float = 0.0) -> kincheckapi.physics_types.PhysicsReport
```

源码：`src/kincheckapi/vibration.py`。

## 导入

```python
from kincheckapi.dynamics import check_resonance_margin
```

## 用途

执行结构化检查：`check_resonance_margin`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `natural_frequencies_hz` | `Sequence[float]` | 必填 | `natural_frequencies_hz` 的公开输入或数据字段。 |
| `excitation_frequencies_hz` | `Sequence[float]` | 必填 | `excitation_frequencies_hz` 的公开输入或数据字段。 |
| `minimum_margin_hz` | `float` | 必填 | `minimum_margin_hz` 的公开输入或数据字段。 |
| `damping_ratio` | `float` | `0.0` | `damping_ratio` 的公开输入或数据字段。 |

## 返回与失败

返回 `PhysicsReport`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应或碰撞冲量。
- 结构、振动和疲劳 API 只对显式线性矩阵、声明材料、应力历程和 S-N 曲线给出可追溯参考结果；自动 BREP 网格、非线性接触、塑性/断裂及非线性振动返回能力边界。

## 相关文档

- [`动力学、结构、振动与疲劳`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
