# `find_singularities`

## API 定义

```python
find_singularities(*, motion_result: Any, assembly: AssemblyModel, options: Any = None) -> SingularityReport
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import find_singularities
```

## 用途

在 MotionResult 的实际采样上计算 Jacobian 秩、最小奇异值和条件数，报告 singular/near-singular 样本。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `Any` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `options` | `Any` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |

## 返回与失败

返回 `SingularityReport`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
