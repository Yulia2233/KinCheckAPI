# `DYNAMICS_MEMBER`

## API 定义

```python
DYNAMICS_MEMBER = 'dynamics.json'
```

源码：`src/kincheckapi/export.py`。

## 导入

```python
from kincheckapi.export import DYNAMICS_MEMBER
```

## 用途

公开常量 `DYNAMICS_MEMBER`。

## 返回与失败

这是只读公共常量，不是可调用函数。

## 模块约束

- 只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。
- 读取前验证 member path、schema、hash 和跨文件引用。
- `require_meshes=True` 时缺少任何必需 mesh 都应失败。

## 相关文档

- [`结果包`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
