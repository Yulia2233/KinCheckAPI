# `write_motion_envelope`

## API 定义

```python
write_motion_envelope(*, report: ClearanceReport, path: str | pathlib.Path) -> None
```

源码：`src/kincheckapi/clearance.py`。

## 导入

```python
from kincheckapi.clearance import write_motion_envelope
```

## 用途

把公开对象确定性写出：`write_motion_envelope`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `report` | `ClearanceReport` | 必填 | `report` 的公开输入或数据字段。 |
| `path` | `str | pathlib.Path` | 必填 | 输入或输出文件路径；具体方向见用途说明。 |

## 返回与失败

返回 `None`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 结果来自三角网格和离散时间采样，不是连续时间无碰撞证明。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
