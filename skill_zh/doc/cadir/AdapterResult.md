# `AdapterResult`

## API 定义

```python
@dataclass(frozen=True)
class AdapterResult:
    assembly: Any
    source_map: Mapping[str, Any]
```

源码：`src/kincheckapi/cadir.py`。

## 导入

```python
from kincheckapi.cadir import AdapterResult
```

## 用途

表示 `AdapterResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `Any` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `source_map` | `Mapping[str, Any]` | 必填 | `source_map` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- XML 根 `model` 必须非空并等于 mapping 的 `root_definition_id`。
- XML、mapping 和 mesh 必须来自同一导出批次；资产解析不得越过 `asset_root`。
- 转换返回装配模型和 source map；转换成功不替代装配、拓扑与 Scenario 校验。
- 读取 `assembly` 作为后续验证输入，并保留 `source_map` 用于回溯 CADIR source ID。

## 相关文档

- [`CADIR 输入转换`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
