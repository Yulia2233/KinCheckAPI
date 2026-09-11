# `scenario_from_dict`

## API 定义

```python
scenario_from_dict(*, assembly: AssemblyModel, data: Mapping[str, Any]) -> Scenario
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import scenario_from_dict
```

## 用途

从已经解析的 mapping 重建与指定 AssemblyModel 绑定的 Scenario；严格校验需另行执行。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `data` | `Mapping[str, Any]` | 必填 | `data` 的公开输入或数据字段。 |

## 返回与失败

返回 `Scenario`。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
