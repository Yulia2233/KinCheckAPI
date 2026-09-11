# CADIR 输入转换

读取 CADIR 导出的 MJCF、mapping 和 mesh，构造可验证的装配模型。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`AdapterResult`](AdapterResult.md) | 类型 | 表示 `AdapterResult` 的公开、可序列化数据结构。 |
| [`convert_mjcf`](convert_mjcf.md) | 函数 | 把 CADIR MJCF XML、mapping JSON 和 mesh 资产转换为 `AdapterResult`。规范的 `mesh_constraints` 将 gear/belt 的端点坐标和 SI 半径保留为已有原生 Constraint，支持行星架参考系下的多坐标方程；显式同轴关节别名保留在 source map 中。原有两关节 Coupling 转换继续支持，可选产品包准备入口位于 `kincheckapi.addon`。 |

## 模块规则

- XML 根 `model` 必须非空并等于 mapping 的 `root_definition_id`。
- XML、mapping 和 mesh 必须来自同一导出批次；资产解析不得越过 `asset_root`。
- 转换返回装配模型和 source map；转换成功不替代装配、拓扑与 Scenario 校验。
