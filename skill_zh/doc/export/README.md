# 结果包

写出、校验和读取后端无关的 .kincheck 运动结果包。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`PACKAGE_SCHEMA_VERSION`](PACKAGE_SCHEMA_VERSION.md) | 常量 | 公开常量 `PACKAGE_SCHEMA_VERSION`。 |
| [`MotionPackage`](MotionPackage.md) | 类型 | 表示 `MotionPackage` 的公开、可序列化数据结构。 |
| [`MotionPackageArtifact`](MotionPackageArtifact.md) | 类型 | 表示 `MotionPackageArtifact` 的公开、可序列化数据结构。 |
| [`export_motion_package`](export_motion_package.md) | 函数 | 把装配、运动结果、校验信息和可选 mesh 写入一个 `.kincheck` 文件。 |
| [`motion_package`](motion_package.md) | 函数 | `export_motion_package()` 的公开兼容别名。 |
| [`read_package`](read_package.md) | 函数 | 严格校验后读取并重建 `.kincheck` 包；失败时抛出 `MotionPackageError`。 |
| [`validate_package`](validate_package.md) | 函数 | 校验 `.kincheck` 的成员路径、schema、hash 和跨文件引用，返回聚合验证结果。 |

## 模块规则

- 只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。
- 读取前验证 member path、schema、hash 和跨文件引用。
- `require_meshes=True` 时缺少任何必需 mesh 都应失败。
