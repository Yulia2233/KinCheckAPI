# `reset_to_home`

## API 定义

```python
reset_to_home(*, scenario: Scenario) -> Scenario
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import reset_to_home
```

## 用途

执行公开操作 `reset_to_home`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | 必填 | 已绑定装配定义的不可变 `Scenario`。 |

## 返回与失败

返回 `Scenario`。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
