# `TransmissionRatioCheck`

## API 定义

```python
@dataclass(frozen=True)
class TransmissionRatioCheck:
    passed: bool
    expected_ratio: float
    measured_ratio: float | None
    relative_error: float | None
    expected_direction: Literal['same', 'opposite']
    measured_direction: Optional[Literal['same', 'opposite']]
    input_joint_id: str
    output_joint_id: str
    input_member: str | None
    output_member: str | None
    fixed_member: str | None
    sample_count: int
    rejected_sample_count: int
    start_time_s: float | None
    end_time_s: float | None
    stage_checks: tuple[_PlanetaryStageEvidence, ...]
    evidence: tuple[Evidence, ...]
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import TransmissionRatioCheck
```

## 用途

表示 `TransmissionRatioCheck` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `passed` | `bool` | 必填 | 结构化布尔结论；必须与 issues 和实际证据一起读取。 |
| `expected_ratio` | `float` | 必填 | 期望传动比的正幅值；方向由 `expected_direction` 单独表达。 |
| `measured_ratio` | `float | None` | 必填 | `measured_ratio` 的公开输入或数据字段。 |
| `relative_error` | `float | None` | 必填 | `relative_error` 的公开输入或数据字段。 |
| `expected_direction` | `Literal['same', 'opposite']` | 必填 | 期望输出与输入同向 `same` 或反向 `opposite`。 |
| `measured_direction` | `Optional[Literal['same', 'opposite']]` | 必填 | `measured_direction` 的公开输入或数据字段。 |
| `input_joint_id` | `str` | 必填 | 稳定且可解析的 `input_joint_id`。 |
| `output_joint_id` | `str` | 必填 | 稳定且可解析的 `output_joint_id`。 |
| `input_member` | `str | None` | `None` | `input_member` 的公开输入或数据字段。 |
| `output_member` | `str | None` | `None` | `output_member` 的公开输入或数据字段。 |
| `fixed_member` | `str | None` | `None` | `fixed_member` 的公开输入或数据字段。 |
| `sample_count` | `int` | `0` | `sample_count` 的公开输入或数据字段。 |
| `rejected_sample_count` | `int` | `0` | `rejected_sample_count` 的公开输入或数据字段。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `stage_checks` | `tuple[_PlanetaryStageEvidence, ...]` | `()` | `stage_checks` 的公开输入或数据字段。 |
| `evidence` | `tuple[Evidence, ...]` | `()` | 支持结论的机器可读证据。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
