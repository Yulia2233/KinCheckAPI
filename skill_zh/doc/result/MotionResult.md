# `MotionResult`

## API 定义

```python
@dataclass(frozen=True)
class MotionResult:
    scenario_id: str
    assembly_id: str
    status: Literal['completed', 'completed_with_warnings', 'partial']
    start_time_s: float
    end_time_s: float
    sample_times_s: tuple[float, ...]
    joint_trajectories: Union[tuple[JointTrajectory, ...], Mapping[str, JointTrajectory]]
    trajectories: tuple[Trajectory, ...]
    constraint_residuals: tuple[ConstraintResidual, ...]
    constraint_equation_residuals: tuple[ConstraintEquationResidual, ...]
    closure_residuals: tuple[ConstraintResidual, ...]
    closure_statuses: Mapping[str, str]
    limit_events: tuple[LimitEvent, ...]
    issues: tuple[SimIssue, ...]
    backend_id: str | None
    backend_version: str | None
    metadata: Mapping[str, Any]
    integration_samples: tuple[IntegrationSample, ...]
    driver_trajectories: tuple[DriverTrajectory, ...]
    traceback: str | None
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import MotionResult
```

## 用途

表示 `MotionResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario_id` | `str` | 必填 | 稳定且可解析的 `scenario_id`。 |
| `assembly_id` | `str` | 必填 | 稳定且可解析的 `assembly_id`。 |
| `status` | `Literal['completed', 'completed_with_warnings', 'partial']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `start_time_s` | `float` | 必填 | 时间窗起点，单位 s。 |
| `end_time_s` | `float` | 必填 | 时间窗终点，单位 s。 |
| `sample_times_s` | `tuple[float, ...]` | 必填 | 严格递增的实际采样时间，单位 s。 |
| `joint_trajectories` | `Union[tuple[JointTrajectory, ...], Mapping[str, JointTrajectory]]` | `()` | `joint_trajectories` 的公开输入或数据字段。 |
| `trajectories` | `tuple[Trajectory, ...]` | `()` | `trajectories` 的公开输入或数据字段。 |
| `constraint_residuals` | `tuple[ConstraintResidual, ...]` | `()` | `constraint_residuals` 的公开输入或数据字段。 |
| `constraint_equation_residuals` | `tuple[ConstraintEquationResidual, ...]` | `()` | `constraint_equation_residuals` 的公开输入或数据字段。 |
| `closure_residuals` | `tuple[ConstraintResidual, ...]` | `()` | `closure_residuals` 的公开输入或数据字段。 |
| `closure_statuses` | `Mapping[str, str]` | default_factory | `closure_statuses` 的公开输入或数据字段。 |
| `limit_events` | `tuple[LimitEvent, ...]` | `()` | `limit_events` 的公开输入或数据字段。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `backend_id` | `str | None` | `None` | 稳定且可解析的 `backend_id`。 |
| `backend_version` | `str | None` | `None` | `backend_version` 的公开输入或数据字段。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |
| `integration_samples` | `tuple[IntegrationSample, ...]` | `()` | `integration_samples` 的公开输入或数据字段。 |
| `driver_trajectories` | `tuple[DriverTrajectory, ...]` | `()` | `driver_trajectories` 的公开输入或数据字段。 |
| `traceback` | `str | None` | `None` | `traceback` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。
- 只有 `completed` 或经审阅的 `completed_with_warnings` 才可进入最终验收；`partial` 只可诊断。
- 空 `sample_times_s` 不能证明任何运动命题。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
