# `child_motion_sign`

## API 定义

```python
child_motion_sign(*, joint: Joint, child_group_id: str, component_groups: Mapping[str, str]) -> float
```

源码：`src/kincheckapi/kinematics_conventions.py`。

## 导入

```python
from kincheckapi.kinematics_conventions import child_motion_sign
```

## 用途

把公开 joint 坐标转换成当前运动树 child group 的运动符号。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `joint` | `Joint` | 必填 | `joint` 的公开输入或数据字段。 |
| `child_group_id` | `str` | 必填 | 稳定且可解析的 `child_group_id`。 |
| `component_groups` | `Mapping[str, str]` | 必填 | `component_groups` 的公开输入或数据字段。 |

## 返回与失败

返回 `float`。

## 模块约束

- 公开 joint 标量方向始终按 `component_b - component_a` 解释。
- 树传播方向可能与 authored connector 顺序相反，必须通过该模块换算符号。
- 不能根据组件名称或树遍历顺序猜测正负方向。

## 相关文档

- [`运动学坐标约定`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
