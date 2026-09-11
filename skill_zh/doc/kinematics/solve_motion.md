# `solve_motion`

## API 定义

```python
solve_motion(*, scenario: Scenario, options: Any = None) -> MotionResult
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import solve_motion
```

## 用途

沿 Scenario 时间窗执行连续运动学求解，返回后端无关的 `MotionResult`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | 必填 | 已绑定装配定义的不可变 `Scenario`。 |
| `options` | `Any` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |

## 返回与失败

返回 `MotionResult`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
