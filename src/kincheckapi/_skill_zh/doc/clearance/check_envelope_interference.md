# `check_envelope_interference`

## API 定义

```python
check_envelope_interference(*, first: ClearanceReport, second: ClearanceReport) -> ClearanceReport
```

源码：`src/kincheckapi/clearance.py`。

## 导入

```python
from kincheckapi.clearance import check_envelope_interference
```

## 用途

比较两个运动包络报告的世界轴对齐包围盒是否重叠。它不会执行三角网格干涉，也不会确认穿透。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `first` | `ClearanceReport` | 必填 | `first` 的公开输入或数据字段。 |
| `second` | `ClearanceReport` | 必填 | `second` 的公开输入或数据字段。 |

## 返回与失败

返回 `ClearanceReport`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 普通干涉、最小间隙和包络结果来自离散采样；跨样本连续证明必须显式调用 `check_continuous_interference()`。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。
- 输入必须是两个 `operation == 'motion_envelope'` 的 `ClearanceReport`。
- `metadata['confirmed_mesh_interference']` 固定为 `False`；发生 overlap 后使用精确 mesh 检查确认。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
