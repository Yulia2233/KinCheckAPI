# `SingularitySample`

## API 定义

```python
@dataclass(frozen=True)
class SingularitySample:
    time_s: float
    status: str
    rank: int
    minimum_singular_value: float | None
    condition_number: float | None
    singular_values: tuple[float, ...]
    joint_positions: Mapping[str, float]
```

源码：`src/kincheckapi/kinematics_analysis.py`。

## 导入

```python
from kincheckapi.kinematics import SingularitySample
```

## 用途

表示 `SingularitySample` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `status` | `str` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `rank` | `int` | 必填 | `rank` 的公开输入或数据字段。 |
| `minimum_singular_value` | `float | None` | 必填 | `minimum_singular_value` 的公开输入或数据字段。 |
| `condition_number` | `float | None` | 必填 | `condition_number` 的公开输入或数据字段。 |
| `singular_values` | `tuple[float, ...]` | `()` | `singular_values` 的公开输入或数据字段。 |
| `joint_positions` | `Mapping[str, float]` | default_factory | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
