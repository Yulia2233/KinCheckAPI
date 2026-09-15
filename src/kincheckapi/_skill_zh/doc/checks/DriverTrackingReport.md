# `DriverTrackingReport`

## API 定义

```python
@dataclass(frozen=True)
class DriverTrackingReport:
    passed: bool
    joint_id: str
    mode: str
    maximum_absolute_error: float
    mean_absolute_error: float
    rms_error: float
    overshoot: float
    undertracking: float
    settling_time_s: float | None
    valid_sample_count: int
    first_failure_time_s: float | None
    tolerance: float
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import DriverTrackingReport
```

## 用途

表示 `DriverTrackingReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `passed` | `bool` | 必填 | 结构化布尔结论；必须与 issues 和实际证据一起读取。 |
| `joint_id` | `str` | 必填 | 稳定且可解析的 joint ID。 |
| `mode` | `str` | 必填 | `mode` 的公开输入或数据字段。 |
| `maximum_absolute_error` | `float` | 必填 | `maximum_absolute_error` 的公开输入或数据字段。 |
| `mean_absolute_error` | `float` | 必填 | `mean_absolute_error` 的公开输入或数据字段。 |
| `rms_error` | `float` | 必填 | `rms_error` 的公开输入或数据字段。 |
| `overshoot` | `float` | 必填 | `overshoot` 的公开输入或数据字段。 |
| `undertracking` | `float` | `0.0` | `undertracking` 的公开输入或数据字段。 |
| `settling_time_s` | `float | None` | 必填 | `settling_time_s`，单位 s，必须为有限值。 |
| `valid_sample_count` | `int` | 必填 | `valid_sample_count` 的公开输入或数据字段。 |
| `first_failure_time_s` | `float | None` | 必填 | `first_failure_time_s`，单位 s，必须为有限值。 |
| `tolerance` | `float` | 必填 | `tolerance` 的公开输入或数据字段。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 检查必须对应明确的对象、时间窗、期望值、阈值和单位。
- 检查对象为空、证据为空或 MotionResult 不完整时不得通过。
- `CheckReport.passed` 是最终布尔结论；同时保留 evidence、issues 和 metadata。
- 装配体整体性检查支持任意数量的 Component；`component_ids=None` 检查整个装配体。
- 机械、容纳/导向和几何连接共同形成连接图；几何连接必须记录米制容差。

## 相关文档

- [`验收检查`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
