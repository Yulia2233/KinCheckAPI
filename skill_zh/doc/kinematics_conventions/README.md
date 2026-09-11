# 运动学坐标约定

定义 authored connector 顺序与运动树传播方向之间的稳定符号约定。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`child_motion_sign`](child_motion_sign.md) | 函数 | 把公开 joint 坐标转换成当前运动树 child group 的运动符号。 |

## 模块规则

- 公开 joint 标量方向始终按 `component_b - component_a` 解释。
- 树传播方向可能与 authored connector 顺序相反，必须通过该模块换算符号。
- 不能根据组件名称或树遍历顺序猜测正负方向。
