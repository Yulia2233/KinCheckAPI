# 离线可视化

把公开运动结果和 mesh 导出为离线 Three.js viewer。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`VIEWER_SCHEMA_VERSION`](VIEWER_SCHEMA_VERSION.md) | 常量 | 公开常量 `VIEWER_SCHEMA_VERSION`。 |
| [`ViewerArtifact`](ViewerArtifact.md) | 类型 | 表示 `ViewerArtifact` 的公开、可序列化数据结构。 |
| [`export_motion_viewer`](export_motion_viewer.md) | 函数 | 导出可离线打开的 Three.js 运动回放资产。 |

## 模块规则

- 可视化只消费公开 AssemblyModel 和 MotionResult，不读取私有后端状态。
- 导出前检查运动状态、实际轨迹和 mesh 资产。
- viewer 用于复核证据，不替代数值验收检查。
