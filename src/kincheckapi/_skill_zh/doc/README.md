# KinCheckAPI API 文档

这些文档按源码模块整理。顶层使用说明在 [`../SKILL.md`](../SKILL.md)；这里按当前任务读取需要的 API，不要一次性加载全部文档。

## 模块

| 模块 | 用途 |
| --- | --- |
| [`cadir`](cadir/README.md) | CADIR MJCF 输入转换 |
| [`assembly`](assembly/README.md) | 装配对象、拓扑和序列化 |
| [`scenario`](scenario/README.md) | 工况、驱动、初态和结果范围 |
| [`kinematics`](kinematics/README.md) | 高层位置/运动求解与分析 |
| [`checks`](checks/README.md) | 运动学验收检查 |
| [`clearance`](clearance/README.md) | 网格干涉、间隙和运动包络 |
| [`result`](result/README.md) | MotionResult 类型、查询和 JSON 输出 |
| [`diagnostics`](diagnostics/README.md) | 结构化问题、证据和诊断报告 |
| [`errors`](errors/README.md) | 稳定的公开异常层级 |
| [`export`](export/README.md) | `.kincheck` 结果包 |
| [`pose`](pose/README.md) | 后端无关的姿态运算 |
| [`trajectory_checks`](trajectory_checks/README.md) | 轨迹窗口统计和限位事件筛选 |
| [`visualization`](visualization/README.md) | 离线运动回放导出 |

## 高级模块

通常从 `kincheckapi.kinematics` 使用高层入口；只有明确需要低层确定性原语时才读取：

- [`kinematics_geometry`](kinematics_geometry/README.md)：姿态传播、Jacobian、mobility 和位置求解原语。
- [`kinematics_conventions`](kinematics_conventions/README.md)：joint 坐标与树传播方向的符号约定。
- [`kinematics_limits`](kinematics_limits/README.md)：关节限位事件检测。
- [`dynamics`](dynamics/README.md)：保留命名空间，当前版本没有公开动力学操作。

## 阅读约定

每个公开符号使用一个同名页面，说明实际签名、导入路径、字段、返回值和失败约束。页面由 `scripts/generate_skill_api_docs.py` 根据公开导出面生成；更新源码 API 后必须重新生成并运行 `--check`。

不为 `_backends`、`_clearance_fcl` 或以下划线开头的实现符号建立公共调用契约。源码和回归测试是最终契约；发现文档差异时修正文档生成规则，不在调用端猜测参数。
