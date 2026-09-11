# `read_package`

## API 定义

```python
read_package(*, path: str | pathlib.Path) -> MotionPackage
```

源码：`src/kincheckapi/export.py`。

## 导入

```python
from kincheckapi.export import read_package
```

## 用途

严格校验后读取并重建 `.kincheck` 包；失败时抛出 `MotionPackageError`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `path` | `str | pathlib.Path` | 必填 | 输入或输出文件路径；具体方向见用途说明。 |

## 返回与失败

返回 `MotionPackage`。

## 模块约束

- 只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。
- 读取前验证 member path、schema、hash 和跨文件引用。
- `require_meshes=True` 时缺少任何必需 mesh 都应失败。

## 相关文档

- [`结果包`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
