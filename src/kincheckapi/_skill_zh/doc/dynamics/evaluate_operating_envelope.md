# `evaluate_operating_envelope`

## API 定义

```python
evaluate_operating_envelope(*, cases: Mapping[str, tuple[kincheckapi.fatigue.StressHistory, kincheckapi.fatigue.FatigueMaterial]], correction: kincheckapi.fatigue.MeanStressCorrection = MeanStressCorrection(method='none', ultimate_strength_pa=None), allowable_damage: float = 1.0, scenario_matrix: kincheckapi.fatigue.ScenarioMatrix | None = None) -> kincheckapi.fatigue.OperatingEnvelopeReport
```

源码：`src/kincheckapi/fatigue.py`。

## 导入

```python
from kincheckapi.dynamics import evaluate_operating_envelope
```

## 用途

执行公开操作 `evaluate_operating_envelope`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `cases` | `Mapping[str, tuple[kincheckapi.fatigue.StressHistory, kincheckapi.fatigue.FatigueMaterial]]` | 必填 | `cases` 的公开输入或数据字段。 |
| `correction` | `kincheckapi.fatigue.MeanStressCorrection` | `MeanStressCorrection(method='none', ultimate_strength_pa=None)` | `correction` 的公开输入或数据字段。 |
| `allowable_damage` | `float` | `1.0` | `allowable_damage` 的公开输入或数据字段。 |
| `scenario_matrix` | `kincheckapi.fatigue.ScenarioMatrix | None` | `None` | `scenario_matrix` 的公开输入或数据字段。 |

## 返回与失败

返回 `OperatingEnvelopeReport`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应或碰撞冲量。
- 结构、振动和疲劳 API 只对显式线性矩阵、声明材料、应力历程和 S-N 曲线给出可追溯参考结果；自动 BREP 网格、非线性接触、塑性/断裂及非线性振动返回能力边界。

## 相关文档

- [`动力学、结构、振动与疲劳`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
