# `convert_mjcf`

## API 定义

```python
convert_mjcf(*, xml_path: str | pathlib.Path, mapping_path: str | pathlib.Path, asset_root: str | pathlib.Path | None = None) -> kincheckapi.cadir.AdapterResult
```

源码：`src/kincheckapi/cadir.py`。

## 导入

```python
from kincheckapi.cadir import convert_mjcf
```

## 用途

把 CADIR MJCF XML、mapping JSON 和 mesh 资产转换为 `AdapterResult`。规范的 `mesh_constraints` 将 gear/belt 的端点坐标和 SI 半径保留为已有原生 Constraint，支持行星架参考系下的多坐标方程；显式同轴关节别名保留在 source map 中。原有两关节 Coupling 转换继续支持，可选产品包准备入口位于 `kincheckapi.addon`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `xml_path` | `str | pathlib.Path` | 必填 | CADIR 导出的 MJCF XML 路径。 |
| `mapping_path` | `str | pathlib.Path` | 必填 | 与 XML 同批次的 mapping JSON 路径。 |
| `asset_root` | `str | pathlib.Path | None` | `None` | mesh 等资产允许解析的根目录。 |

## 返回与失败

返回 `AdapterResult`。

## 模块约束

- XML 根 `model` 必须非空并等于 mapping 的 `root_definition_id`。
- XML、mapping 和 mesh 必须来自同一导出批次；资产解析不得越过 `asset_root`。
- 转换返回装配模型和 source map；转换成功不替代装配、拓扑与 Scenario 校验。

## 相关文档

- [`CADIR 输入转换`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
