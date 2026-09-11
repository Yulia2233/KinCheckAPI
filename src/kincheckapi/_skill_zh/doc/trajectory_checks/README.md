# 轨迹工具

计算轨迹时间窗指标并筛选限位事件。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`TrajectoryWindowMetrics`](TrajectoryWindowMetrics.md) | 类型 | 表示 `TrajectoryWindowMetrics` 的公开、可序列化数据结构。 |
| [`limit_events_in_window`](limit_events_in_window.md) | 函数 | 按 joint ID 和时间窗筛选已经记录的 `LimitEvent`。 |
| [`normalize_position_bounds`](normalize_position_bounds.md) | 函数 | 把可选位置边界规范化为每轴 `(lower, upper)` 的只读 mapping，并拒绝无效边界。 |
| [`trajectory_window_metrics`](trajectory_window_metrics.md) | 函数 | 在明确时间窗内计算单条组件或 connector 轨迹的样本索引、路径长度和世界坐标 bounds。 |

## 模块规则

- 时间窗必须落在实际采样范围内，并至少包含足够样本。
- 空窗口和不合法位置边界不得解释为通过。
- 路径长度和 bounds 都来自离散样本。
