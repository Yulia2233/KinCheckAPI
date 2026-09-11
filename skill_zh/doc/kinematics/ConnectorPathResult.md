# `ConnectorPathResult`

## API 定义

```python
@dataclass(frozen=True)
class ConnectorPathResult:
    component_id: str
    connector_id: str
    times_s: tuple[float, ...]
    positions_m: tuple[tuple[float, float, float], ...]
    path_length_m: float
    bounds_m: Mapping[str, tuple[float, float]]
    start_position_m: tuple[float, float, float] | None
    end_position_m: tuple[float, float, float] | None
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/kinematics_analysis.py`。

## 导入

```python
from kincheckapi.kinematics import ConnectorPathResult
```

## 用途

表示 `ConnectorPathResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `connector_id` | `str` | 必填 | 稳定且可解析的 connector ID。 |
| `times_s` | `tuple[float, ...]` | 必填 | `times_s`，单位 s，必须为有限值。 |
| `positions_m` | `tuple[tuple[float, float, float], ...]` | 必填 | `positions_m`，单位 m，必须为有限值。 |
| `path_length_m` | `float` | 必填 | `path_length_m`，单位 m，必须为有限值。 |
| `bounds_m` | `Mapping[str, tuple[float, float]]` | 必填 | `bounds_m`，单位 m，必须为有限值。 |
| `start_position_m` | `tuple[float, float, float] | None` | 必填 | `start_position_m`，单位 m，必须为有限值。 |
| `end_position_m` | `tuple[float, float, float] | None` | 必填 | `end_position_m`，单位 m，必须为有限值。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |

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
