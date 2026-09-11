# `solve_position`

## API 定义

```python
solve_position(*, assembly: AssemblyModel, joint_positions: Optional[Mapping[str, float]] = None, pose_targets: Sequence[PoseTarget] = (), options: Union[PositionSolveOptions, Mapping[str, Any], NoneType] = None) -> PositionResult
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import solve_position
```

## 用途

求解指定运动学问题：`solve_position`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `joint_positions` | `Optional[Mapping[str, float]]` | `None` | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |
| `pose_targets` | `Sequence[PoseTarget]` | `()` | `pose_targets` 的公开输入或数据字段。 |
| `options` | `Union[PositionSolveOptions, Mapping[str, Any], NoneType]` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |

## 返回与失败

返回 `PositionResult`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
