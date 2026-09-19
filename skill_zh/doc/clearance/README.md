# 几何安全

在离散运动样本上检查网格干涉、最小间隙和运动包络。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`ClearanceReport`](ClearanceReport.md) | 类型 | 表示 `ClearanceReport` 的公开、可序列化数据结构。 |
| [`EnvelopeSample`](EnvelopeSample.md) | 类型 | 表示 `EnvelopeSample` 的公开、可序列化数据结构。 |
| [`MinimumClearance`](MinimumClearance.md) | 类型 | 表示 `MinimumClearance` 的公开、可序列化数据结构。 |
| [`MotionEnvelope`](MotionEnvelope.md) | 类型 | 表示 `MotionEnvelope` 的公开、可序列化数据结构。 |
| [`SamplingScope`](SamplingScope.md) | 类型别名 | 定义 `SamplingScope` 使用的公开类型约定。 |
| [`check_continuous_interference`](check_continuous_interference.md) | 函数 | 在声明的分段刚体位姿插值下，跨相邻轨迹样本保守地检查显式组件对，并返回 TOI 区间证据。 |
| [`check_envelope_interference`](check_envelope_interference.md) | 函数 | 比较两个运动包络报告的世界轴对齐包围盒是否重叠。它不会执行三角网格干涉，也不会确认穿透。 |
| [`check_interference`](check_interference.md) | 函数 | 检查离散运动样本中的指定组件对是否发生网格穿透。 |
| [`create_motion_envelope`](create_motion_envelope.md) | 函数 | 为明确组件生成离散运动包络，供后续空间干涉分析。 |
| [`measure_minimum_clearance`](measure_minimum_clearance.md) | 函数 | 测量离散运动样本中指定组件对的最小带符号间隙。 |
| [`write_motion_envelope`](write_motion_envelope.md) | 函数 | 把公开对象确定性写出：`write_motion_envelope`。 |

## 模块规则

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 普通干涉、最小间隙和包络结果来自离散采样；跨样本连续证明必须显式调用 `check_continuous_interference()`。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。
