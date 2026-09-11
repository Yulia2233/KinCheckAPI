# `trajectory_window_metrics`

## API 定义

```python
trajectory_window_metrics(*, trajectory: Trajectory, start_time_s: float | None, end_time_s: float | None) -> TrajectoryWindowMetrics
```

源码：`src/kincheckapi/trajectory_checks.py`。

## 导入

```python
from kincheckapi.trajectory_checks import trajectory_window_metrics
```

## 用途

在明确时间窗内计算单条组件或 connector 轨迹的样本索引、路径长度和世界坐标 bounds。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `trajectory` | `Trajectory` | 必填 | `trajectory` 的公开输入或数据字段。 |
| `start_time_s` | `float | None` | 必填 | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | 必填 | 时间窗终点，单位 s。 |

## 返回与失败

返回 `TrajectoryWindowMetrics`。

## 模块约束

- 时间窗必须落在实际采样范围内，并至少包含足够样本。
- 空窗口和不合法位置边界不得解释为通过。
- 路径长度和 bounds 都来自离散样本。

## 相关文档

- [`轨迹工具`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
