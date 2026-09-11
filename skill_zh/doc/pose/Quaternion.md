# `Quaternion`

## API 定义

```python
Quaternion = tuple
```

源码：`src/kincheckapi/pose.py`。

## 导入

```python
from kincheckapi.pose import Quaternion
```

## 用途

定义 `Quaternion` 使用的公开类型约定。

## 返回与失败

这是类型约定，不是可调用函数。

## 模块约束

- 位置使用 m，四元数顺序固定为 xyzw。
- 输入向量和四元数必须有限；零范数四元数无效。
- 明确 parent、child、actual 和 expected 的参考坐标系。

## 相关文档

- [`姿态运算`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
