# `SpeedDriver`

## API 定义

```python
@dataclass(frozen=True)
class SpeedDriver:
    joint_id: str
    profile: MotionProfile
    active_interval_s: tuple[float, float] | None
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import SpeedDriver
```

## 用途

表示 `SpeedDriver` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `joint_id` | `str` | 必填 | 稳定且可解析的 joint ID。 |
| `profile` | `MotionProfile` | 必填 | `profile` 的公开输入或数据字段。 |
| `active_interval_s` | `tuple[float, float] | None` | `None` | `active_interval_s`，单位 s，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
