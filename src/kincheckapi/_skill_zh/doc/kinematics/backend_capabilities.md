# `backend_capabilities`

## API 定义

```python
backend_capabilities() -> KinematicCapabilities
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import backend_capabilities
```

## 用途

执行公开操作 `backend_capabilities`。

## 返回与失败

返回 `KinematicCapabilities`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
