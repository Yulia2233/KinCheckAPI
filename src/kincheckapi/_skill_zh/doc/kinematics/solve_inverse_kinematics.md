# `solve_inverse_kinematics`

## API 定义

```python
solve_inverse_kinematics(*, assembly: AssemblyModel, target: Union[PoseTarget, Mapping[str, Any]], initial_joint_positions: Optional[Mapping[str, float]] = None, joint_limits: Optional[Mapping[str, Sequence[float]]] = None, solution_selection: Literal['first', 'lowest_residual', 'closest_to_initial'] = 'first', options: Union[kincheckapi.kinematics_ik.IKOptions, Mapping[str, Any], NoneType] = None) -> kincheckapi.kinematics_ik.IKSolutionSet
```

源码：`src/kincheckapi/kinematics_ik.py`。

## 导入

```python
from kincheckapi.kinematics import solve_inverse_kinematics
```

## 用途

求解指定运动学问题：`solve_inverse_kinematics`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `target` | `Union[PoseTarget, Mapping[str, Any]]` | 必填 | `target` 的公开输入或数据字段。 |
| `initial_joint_positions` | `Optional[Mapping[str, float]]` | `None` | `initial_joint_positions` 的公开输入或数据字段。 |
| `joint_limits` | `Optional[Mapping[str, Sequence[float]]]` | `None` | `joint_limits` 的公开输入或数据字段。 |
| `solution_selection` | `Literal['first', 'lowest_residual', 'closest_to_initial']` | `'first'` | `solution_selection` 的公开输入或数据字段。 |
| `options` | `Union[kincheckapi.kinematics_ik.IKOptions, Mapping[str, Any], NoneType]` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |

## 返回与失败

返回 `IKSolutionSet`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
