---
name: sca-kincheckapi-zh
description: 使用 KinCheckAPI 验证 CAD 机构的拓扑、运动、传动、姿态、限位和几何安全。消费成品 .scadpkg 装配包中的定义、occurrence 图、几何及验收所需的 interface.* 标签，产出独立 Python 验证程序和结构化验收结果。用于验证先行的设计迭代或已有产品包检查；继续支持现有 MJCF 模型目录验证程序。
---

# KinCheckAPI 验证程序技能（v0.8.0）

把用户的机构要求固化成可执行的 Python 验收程序，再构建模型并用该程序驱动设计迭代。固定遵循下面的顺序：

```text
用户验收命题
    -> 先编写 verification/ Python 程序
    -> 静态检查验证程序及其输入契约
    -> 交给主 SimpleCADAPI skill 在建模环境构建机构
    -> capture(result, "product.scadpkg")
    -> 插件在独立环境校验产品包并在自己的工作目录准备 MJCF
    -> verification.verify(model_dir)
    -> 将失败证据交回主 skill 修改几何
    -> 重新 capture 并验证，直到满足原验收命题
```

先读本文完成工作流，再按实际调用的模块打开 `doc/<module>/<api>.md`；API 索引见 [`doc/README.md`](doc/README.md)。

首次使用前必须执行下文的运行时关卡并遵守产品包消费契约。对于已有产品包，
直接按验收命题开始消费，无需重新建模。本插件永不修改源几何、产品包成员或建模模块。
几何变更交回主 `simplecadapi` skill，重新 `capture` 后才能继续分析。

## 默认交付

本 skill 的主要交付物是一个独立的 Python 验证目录，不是验证报告、`.kincheck` 文件或建模源码：

```text
verification/
├── __init__.py
├── verify.py              # 必须：Python API 和 CLI 入口
└── checks.py              # 可选：检查定义较多时拆分
```

最小交付可以只有 `verification/verify.py`。验证程序必须：

- 只依赖 KinCheckAPI 公开 API 和 Python 标准库；
- 以 `model_dir` 作为模型输入，不导入 SimpleCADAPI 建模模块；
- 将验收对象 ID、驱动、时间窗、采样周期、阈值、单位和检查范围写入代码；
- 返回结构化 KinCheckAPI 结果，并在 CLI 严格模式下以非零退出表示未通过；
- 可以在另一个符合相同输入契约的模型上重复运行。

`.kincheck`、JSON、图片和可视化仅在用户明确要求调试、归档或回放时生成，不属于默认交付。

## 装配体整体性检查

运动时间窗求解完成后，检查被选中的 Component 是否在每个状态仍保持为一个整体：

```python
from kincheckapi import check_assembly_integrity

integrity = check_assembly_integrity(
    assembly=assembly,
    motion_result=motion,
    asset_root=model_dir,
    geometric_connection_pairs=(("component.a", "component.b"),),
    geometric_connection_tolerance_m=1e-4,
)
integrity.raise_if_failed()
```

两个相距很远、没有任何有效关系的 Component 即使没有发生碰撞，也属于装配体断开并必须失败。滑动件可以在导向件内保留间隙，但一旦离开声明的容纳区间或有效行程就必须失败。每个几何连接都必须声明有限、非负的米制容差。当 `sampling_scope="motion_result"` 时检查 MotionResult 的每个采样；`sampling_scope="initial"` 只代表静态检查。

## 运行时 CLI

首次导入、执行验证程序或准备产品包之前，必须在插件独立环境运行描述符中的原始探针：

```bash
kincheck doctor --addon --format json
```

只有退出码 0 才能继续。失败时根据 `checks` 指明缺失运行时并停止，不得跳过分析、
静默切换 Python 或把插件装入建模环境。探针只做本地依赖导入，不联网、不检查许可证、
不启动 GUI。`sca` 安装时探针失败只警告，但首次使用仍必须通过。
环境创建及修复见 [`doc/guides/addon-contract.md`](doc/guides/addon-contract.md)。

产品包 API 和 CLI 也会强制执行该探针。只使用原有 MJCF API 的用户仍可执行
`kincheck doctor --format json`，无需安装可选 SDK。

验证程序必须暴露 `verify(model_dir)`，返回明确的结构化验收结果；`None` 或任意对象
属于输入错误。消费结构化 JSON 的 `status`、`issues` 和进程退出码，
不要解析人类可读的 stdout。使用 `kincheck-skill-pack --language zh --archive --adapters` 生成
可移植 Skill 产物。

## 模型输入契约

插件的成品输入是根定义为装配体的 `.scadpkg`。消费前阅读
[`doc/guides/addon-contract.md`](doc/guides/addon-contract.md)。格式规范位于主
`simplecadapi` skill 的 `references/scadpkg-format.md`，本插件附有
[`doc/guides/scadpkg-format.md`](doc/guides/scadpkg-format.md) 副本。
没有主 skill 时，以已安装 `simplecadapi/contracts/` 内的 JSON Schema 为准。

准备前按精确的零件 occurrence ID 声明必需 `interface.*` 标签。完全通过 joint 和
connector ID 表达的检查默认不要求标签。所需标签缺失必须报告完整名称和 occurrence，
不得通过几何近似；一个标签下的多个实体必须全部保留。

产品包长度为毫米；SDK 导出器把位置及网格比例换算为米，不得对生成的 MJCF 再次缩放。
occurrence 变换相对父节点，不能将定义局部坐标当成世界坐标。MJCF 四元数为 `wxyz`，
KinCheckAPI Pose 为 `xyzw`，由 `convert_mjcf()` 转换。公开关节正方向是
`component_b - component_a`，使用已文档化的运动学符号规则。

产品包准备会生成以下目录；现有验证程序仍然只接收一个模型目录：

```text
model/
├── scene.xml
├── scene.mapping.json
└── meshes/                # XML/mapping 引用的资产
```

在 `verify.py` 中显式拼接这三个路径并调用 `convert_mjcf()`；不得扫描目录猜测 XML、mapping 或对象关系。输入必须满足：

- XML 根元素有非空 `model` 属性，且等于 mapping 的 `root_definition_id`；
- XML、mapping 和 mesh 来自同一次 SimpleCADAPI/CADIR 导出；
- mesh 路径规范化后仍位于 `model_dir` 内；
- mapping 中的 source ID、XML name、joint、site、equality 和 mesh 引用可双向解析；
- 不使用已删除的 `read_artifact()`、`validate_artifact()`、`convert_artifact()` 或 `convert_live_assembly()`。

若现有导出器使用其他文件名，优先调整 SimpleCADAPI 导出目标以满足该契约，不在验证程序中加入模糊发现逻辑。

## 验证先行

### 1. 固化验收命题

在建模前明确：

- 要证明的机构事实；
- joint、component、connector 或 component pair 的稳定 ID；
- 初态、驱动、时间窗和采样周期；
- 期望运动范围、方向、传动关系、轨迹或姿态；
- 残差、限位、干涉或间隙阈值及 SI 单位；
- 哪些条件属于通过、失败或未完成。

信息不足时把缺失项列为建模接口要求，不根据名称、齿数或几何外观猜测。

### 2. 先写验证程序

`verify.py` 至少公开以下入口：

```python
from pathlib import Path


def verify(model_dir: str | Path):
    """验证一个满足固定目录契约的导出模型并返回结构化检查结果。"""
    ...


def main() -> int:
    ...


if __name__ == "__main__":
    raise SystemExit(main())
```

CLI 的默认用法必须简单且稳定：

```bash
python verification/verify.py path/to/model
```

在模型存在前，至少完成 Python 语法检查、导入检查，以及路径/参数失败分支检查。不要先造一个临时模型再反推验收条件。

### 3. 再用 SimpleCADAPI 构建模型

验证程序完成后，交给主 `simplecadapi` skill 在建模环境创建几何、装配关系、稳定 ID
和所需公开标签，并 capture 为 `.scadpkg`。再在插件独立环境调用 `prepare_package()`
或 `kincheck verify-package` 准备符合输入契约的目录。建议项目布局：

```text
project/
├── verification/          # 先写；KinCheckAPI 验收程序
├── simplecadapi/          # 后写；模型实现
└── model/                 # SimpleCADAPI/CADIR 导出；验证程序输入
```

KinCheckAPI 验证目录不得依赖 `simplecadapi/` 的 Python 模块。模型实现可以改变，但只要验收命题未改变，验证程序中的阈值和检查范围必须保持稳定。

### 4. 运行并迭代模型

把准备后的 `model_dir` 传给验证程序。失败时读取 error code、object ID、source path、
Evidence、失败时刻和建议动作，再回到主 `simplecadapi` skill 修改所属建模源码并重新
capture；消费新产品包后运行同一验证程序。插件内部不得修改几何或补造缺失接口。

禁止为了让当前模型通过而：

- 放宽阈值或缩短要求的运动范围；
- 减少采样以跳过失败时刻；
- 删除失败检查或把显式空集合扩大为全部对象；
- 添加没有物理依据的碰撞排除；
- 把 `partial`、空样本、能力缺失或异常中断包装成通过。

只有用户明确修改验收命题时，才同步修改验证程序。

## `verify.py` 标准骨架

```python
import argparse
from pathlib import Path

from kincheckapi.assembly import validate_assembly, validate_topology
from kincheckapi.cadir import convert_mjcf
from kincheckapi.checks import CheckSpec, run_checks
from kincheckapi.errors import KinCheckError
from kincheckapi.kinematics import solve_motion
from kincheckapi.scenario import (
    add_joint_speed_driver,
    create_scenario,
    request_joint_result,
    set_run_duration,
    set_sample_period,
    validate_scenario,
)

INPUT_JOINT_ID = "joint.input"
RUN_DURATION_S = 1.0
SAMPLE_PERIOD_S = 0.01


def verify(model_dir: str | Path):
    root = Path(model_dir).expanduser().resolve()
    converted = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    assembly = converted.assembly
    validate_assembly(assembly=assembly).raise_if_failed()
    validate_topology(assembly=assembly).raise_if_failed()

    condition = create_scenario(scenario_id="verification.nominal", assembly=assembly)
    condition = add_joint_speed_driver(
        scenario=condition,
        joint_id=INPUT_JOINT_ID,
        speed_rad_s_or_m_s=1.0,
        start_time_s=0.0,
        end_time_s=RUN_DURATION_S,
    )
    condition = set_run_duration(scenario=condition, duration_s=RUN_DURATION_S)
    condition = set_sample_period(scenario=condition, period_s=SAMPLE_PERIOD_S)
    condition = request_joint_result(scenario=condition, joint_id=INPUT_JOINT_ID)
    validate_scenario(scenario=condition).raise_if_failed()

    motion = solve_motion(scenario=condition)
    motion.raise_if_failed()
    suite = run_checks(
        assembly=assembly,
        scenario=condition,
        motion_result=motion,
        checks=(CheckSpec(
            check_id="constraint-residuals",
            check_type="constraint_residuals",
            parameters={"position_tolerance_m": 1e-6},
        ),),
    )
    suite.raise_if_failed()
    return suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.model_dir)
    except KinCheckError as error:
        print(error)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

根据用户命题替换骨架中的 ID、驱动和检查，不能把示例值直接当成通用验收条件。Scenario 设置函数返回新的不可变对象，必须接住每次返回值。

## 通过规则

1. “程序没有抛异常”不是验收命题；必须执行与用户要求对应的检查。
2. `MotionResult.status == "partial"`、`capability_failed`、空采样、空测量和空组件对都不能通过。
3. 只接受 `completed` 或 `completed_with_warnings`；后者必须审阅 warnings 和 issues。
4. `completed` 只表示指定时间窗完成，不能自动声称完成整圈、全行程或完整工作空间。
5. 显式指定检查对象；显式 `()` 不得解释为“全部”。
6. 统一使用 SI：m、rad、s、m/s、rad/s。
7. 网格安全检查只证明离散样本上的结果，不是连续时间无碰撞证明。
8. 运动学证据不等于动力学、强度、制造或法规结论。

## 按事实选择 API

| 要证明的事实 | 首选 API 文档 |
| --- | --- |
| 模型转换 | [`convert_mjcf`](doc/cadir/convert_mjcf.md) |
| 装配引用、Ground、拓扑 | [`validate_assembly`](doc/assembly/validate_assembly.md)、[`validate_topology`](doc/assembly/validate_topology.md) |
| 整个装配体保持为一个整体 | [`check_assembly_integrity`](doc/checks/check_assembly_integrity.md)、[`ContainmentRelation`](doc/checks/ContainmentRelation.md) |
| 运动树和自由度 | [`build_kinematic_tree`](doc/assembly/build_kinematic_tree.md)、[`analyze_dofs`](doc/kinematics/analyze_dofs.md)、[`analyze_mobility`](doc/kinematics/analyze_mobility.md) |
| 指定姿态或连续运动 | [`solve_position`](doc/kinematics/solve_position.md)、[`solve_motion`](doc/kinematics/solve_motion.md) |
| 失败前运动证据 | [`try_solve_motion`](doc/kinematics/try_solve_motion.md) |
| 闭环和约束 | [`validate_closures`](doc/kinematics/validate_closures.md)、[`check_constraint_residuals`](doc/checks/check_constraint_residuals.md) |
| 传动关系 | [`check_transmission_ratio`](doc/checks/check_transmission_ratio.md) |
| 姿态、轨迹、限位 | `doc/checks/` 中对应的 `check_*.md` |
| 奇异性、可达性、工作空间 | `doc/kinematics/` 中对应的分析文档 |
| 干涉、间隙、运动包络 | `doc/clearance/` 和 `doc/checks/` |
| 结果读取和可选导出 | `doc/result/`、`doc/export/` |
| 错误和诊断 | [`diagnostics`](doc/diagnostics/README.md)、[`errors`](doc/errors/README.md) |

## 失败输出

所有公开错误与验证结果使用同一个无参数输出协议：直接 `print(error)` 或 `print(result)`；严格 CLI 流程调用 `raise_if_failed()` 并返回非零退出码。机器消费时使用 `to_dict()`，不要根据 `issues` 手工拼接另一套错误正文。

`partial` 或求解失败时，保留 `last_valid_result`、失败时刻和诊断，但不得宣称验证通过。后端不可用或能力不支持时报告能力缺失，不使用替代计算伪装成功。

## 参考文档

- [`doc/guides/verification-procedure.md`](doc/guides/verification-procedure.md)：验证程序优先的固定执行顺序。
- [`doc/guides/evidence-and-pass-rules.md`](doc/guides/evidence-and-pass-rules.md)：统一通过规则。
- [`doc/guides/kinematic-correctness.md`](doc/guides/kinematic-correctness.md)：运动学正确性的分层证据。
- [`doc/guides/failure-diagnosis.md`](doc/guides/failure-diagnosis.md)：失败、partial 和结构化诊断。
- [`doc/README.md`](doc/README.md)：按模块的 API 索引。

## v0.7 刚体动力学验收

KinCheckAPI v0.7 只验收一般刚体状态、约束、接触/冲量、驱动工况、反力、能量
和可重放载荷历程。保留单位、坐标帧、source ID、时间覆盖、收敛和结构化失败
证据。结构网格、应力、变形、结构振动和疲劳属于 FEACheckAPI，不得在这里导入
或推断。

## v0.6.1-v0.6.3 动力学验收

真实 BREP 物性、显式惯量和树形静力见[物性与静力流程](doc/guides/physical-statics.md)；v0.6.1-v0.6.3 更新说明覆盖标量树逆动力学、有限驱动正动力学和给定外力的接触/摩擦容量。逐操作探测能力并保留结构化失败证据；闭环动力学和接触响应/碰撞冲量仍是能力边界。
