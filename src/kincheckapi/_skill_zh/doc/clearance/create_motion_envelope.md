# `create_motion_envelope`

## API 定义

```python
create_motion_envelope(*, assembly: AssemblyModel, motion_result: MotionResult, component_ids: Optional[Sequence[str]] = None, start_time_s: float | None = None, end_time_s: float | None = None, sampling_scope: Literal['motion_result', 'solver_steps'] = 'motion_result', asset_root: str | pathlib.Path | None = None) -> ClearanceReport
```

源码：`src/kincheckapi/clearance.py`。

## 导入

```python
from kincheckapi.clearance import create_motion_envelope
```

## 用途

为明确组件生成离散运动包络，供后续空间干涉分析。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_ids` | `Optional[Sequence[str]]` | `None` | 显式指定的 `component_ids` 集合。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | `sampling_scope` 的公开输入或数据字段。 |
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
