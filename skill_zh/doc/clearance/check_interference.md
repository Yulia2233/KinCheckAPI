# `check_interference`

## API 定义

```python
check_interference(*, assembly: AssemblyModel, motion_result: MotionResult, component_pairs: Optional[Sequence[Sequence[str]]] = None, excluded_pairs: Sequence[Sequence[str]] = (), penetration_tolerance_m: float = 0.0, start_time_s: float | None = None, end_time_s: float | None = None, sampling_scope: Literal['motion_result', 'solver_steps'] = 'motion_result', max_sample_period_s: float | None = None, asset_root: str | pathlib.Path | None = None) -> ClearanceReport
```

源码：`src/kincheckapi/clearance.py`。

## 导入

```python
from kincheckapi.clearance import check_interference
```

## 用途

检查离散运动样本中的指定组件对是否发生网格穿透。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_pairs` | `Optional[Sequence[Sequence[str]]]` | `None` | `component_pairs` 的公开输入或数据字段。 |
| `excluded_pairs` | `Sequence[Sequence[str]]` | `()` | `excluded_pairs` 的公开输入或数据字段。 |
| `penetration_tolerance_m` | `float` | `0.0` | `penetration_tolerance_m`，单位 m，必须为有限值。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | `sampling_scope` 的公开输入或数据字段。 |
| `max_sample_period_s` | `float | None` | `None` | `max_sample_period_s`，单位 s，必须为有限值。 |
| `asset_root` | `str | pathlib.Path | None` | `None` | mesh 等资产允许解析的根目录。 |

## 返回与失败

返回 `ClearanceReport`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 结果来自三角网格和离散时间采样，不是连续时间无碰撞证明。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
