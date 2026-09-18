# `check_reachability`

## API 定义

```python
check_reachability(*, assembly: AssemblyModel, target: Any, options: Any = None, joint_positions: Optional[Mapping[str, float]] = None, solver_options: Any = None) -> ReachabilityResult
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import check_reachability
```

## 用途

执行结构化检查：`check_reachability`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `target` | `Any` | 必填 | `target` 的公开输入或数据字段。 |
| `options` | `Any` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |
| `joint_positions` | `Optional[Mapping[str, float]]` | `None` | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |
| `solver_options` | `Any` | `None` | `solver_options` 的公开输入或数据字段。 |

## 返回与失败

返回 `ReachabilityResult`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
