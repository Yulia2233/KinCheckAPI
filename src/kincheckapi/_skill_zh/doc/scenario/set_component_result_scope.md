# `set_component_result_scope`

## API 定义

```python
set_component_result_scope(*, scenario: Scenario, scope: ComponentResultScope | str) -> Scenario
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import set_component_result_scope
```

## 用途

选择组件轨迹记录范围。`all` 始终记录全部组件；`requested` 在请求列表非空时仅记录所请求对象，在空列表时保留历史兼容行为并记录全部组件。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | 必填 | 已绑定装配定义的不可变 `Scenario`。 |
| `scope` | `ComponentResultScope | str` | 必填 | `scope` 的公开输入或数据字段。 |

## 返回与失败

返回 `Scenario`。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。
- `requested` + 空请求列表会扩大为全部组件，这是明确的历史兼容特例。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
