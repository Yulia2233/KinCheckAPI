# `check_continuous_interference`

## API 定义

```python
check_continuous_interference(*, assembly: AssemblyModel, motion_result: MotionResult, component_pairs: Sequence[Sequence[str]], options: Union[ContinuousInterferenceOptions, Mapping[str, Any], NoneType] = None, start_time_s: float | None = None, end_time_s: float | None = None, asset_root: str | pathlib.Path | None = None) -> ContinuousInterferenceReport
```

源码：`src/kincheckapi/clearance.py`。

## 导入

```python
from kincheckapi.clearance import check_continuous_interference
```

## 用途

在声明的分段刚体位姿插值下，跨相邻轨迹样本保守地检查显式组件对，并返回 TOI 区间证据。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_pairs` | `Sequence[Sequence[str]]` | 必填 | `component_pairs` 的公开输入或数据字段。 |
| `options` | `Union[ContinuousInterferenceOptions, Mapping[str, Any], NoneType]` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `asset_root` | `str | pathlib.Path | None` | `None` | mesh 等资产允许解析的根目录。 |

## 返回与失败

返回 `ContinuousInterferenceReport`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 普通干涉、最小间隙和包络结果来自离散采样；跨样本连续证明必须显式调用 `check_continuous_interference()`。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
