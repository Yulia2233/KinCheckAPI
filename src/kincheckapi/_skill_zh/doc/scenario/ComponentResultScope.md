# `ComponentResultScope`

## API 定义

```python
class ComponentResultScope(str, Enum): ...
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import ComponentResultScope
```

## 用途

定义 `ComponentResultScope` 接受的稳定枚举值。

## 枚举值

| 成员 | 值 |
| --- | --- |
| `REQUESTED` | `requested` |
| `ALL` | `all` |

## 返回与失败

使用枚举成员或其稳定字符串值，避免自行发明未定义状态。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
