# `SamplingScope`

## API 定义

```python
SamplingScope = Literal
```

源码：`src/kincheckapi/clearance.py`。

## 导入

```python
from kincheckapi.clearance import SamplingScope
```

## 用途

定义 `SamplingScope` 使用的公开类型约定。

## 返回与失败

这是类型约定，不是可调用函数。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 普通干涉、最小间隙和包络结果来自离散采样；跨样本连续证明必须显式调用 `check_continuous_interference()`。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
