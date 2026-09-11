# `VIEWER_SCHEMA_VERSION`

## API 定义

```python
VIEWER_SCHEMA_VERSION = 'kincheck.viewer/1.0'
```

源码：`src/kincheckapi/visualization.py`。

## 导入

```python
from kincheckapi.visualization import VIEWER_SCHEMA_VERSION
```

## 用途

公开常量 `VIEWER_SCHEMA_VERSION`。

## 返回与失败

这是只读公共常量，不是可调用函数。

## 模块约束

- 可视化只消费公开 AssemblyModel 和 MotionResult，不读取私有后端状态。
- 导出前检查运动状态、实际轨迹和 mesh 资产。
- viewer 用于复核证据，不替代数值验收检查。

## 相关文档

- [`离线可视化`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
