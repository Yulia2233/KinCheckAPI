# 连续碰撞证据

定义跨轨迹样本区间的保守连续干涉选项、接触事件和可审计报告。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`ContinuousInterferenceOptions`](ContinuousInterferenceOptions.md) | 类型 | 表示 `ContinuousInterferenceOptions` 的公开、可序列化数据结构。 |
| [`ContinuousContactEvent`](ContinuousContactEvent.md) | 类型 | 表示 `ContinuousContactEvent` 的公开、可序列化数据结构。 |
| [`ContinuousInterferenceReport`](ContinuousInterferenceReport.md) | 类型 | 表示 `ContinuousInterferenceReport` 的公开、可序列化数据结构。 |

## 模块规则

- 连续通过只表示声明的位姿插值和速度上界下已取得完整保守证据；不能外推到未记录的非刚体或动力学运动。
- `failed` 记录接触或间隙违规；`indeterminate` 表示预算、时间轴或几何证据不足，不能当作通过。
- 事件中的最早接触时间是上界，`certainty`、查询次数、细分次数和 options 必须随报告保存。
