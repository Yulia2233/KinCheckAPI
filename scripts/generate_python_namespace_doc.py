#!/usr/bin/env python3
"""Generate the complete public API namespace table for the design docs."""

from __future__ import annotations

import inspect
import importlib
import enum
import re
import sys
import typing
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import generate_skill_api_docs as api_docs


CLI_ROWS = (
    ("kincheck doctor", "命令", "检查 Python、物理后端、FCL、trimesh 和 rtree 的运行环境。", "已实现"),
    ("kincheck validate-model", "命令", "读取并校验一个 CADIR MJCF、mapping 和 mesh 模型目录。", "已实现"),
    ("kincheck verify", "命令", "使用独立的 `verification/verify.py` 对一个模型目录执行验收程序。", "已实现"),
    ("kincheck-skill-pack", "命令", "生成中英文 Agent Skill archive 和 harness 适配器。", "已实现"),
)


NAMESPACE_PURPOSES = {
    "cadir": "CADIR MJCF、mapping 和 mesh 输入转换",
    "assembly": "装配模型、组件关系、关节、闭环、拓扑和序列化",
    "scenario": "运动工况、初态、驱动、限位、时间和采样",
    "kinematics": "位置/连续运动求解以及自由度、Jacobian、可达性、奇异性和工作空间分析",
    "checks": "对装配和运动结果执行显式、结构化的验收检查，包括整体性检查",
    "clearance": "使用真实网格检查干涉、最小间隙和运动包络",
    "result": "读取运动结果、轨迹、状态、残差和事件",
    "diagnostics": "聚合、解释、格式化和持久化结构化诊断",
    "errors": "稳定的 KinCheckAPI 异常层级和错误上下文",
    "export": "导出、读取和校验 `.kincheck` 运动结果包",
    "pose": "后端无关的姿态、四元数和坐标变换",
    "trajectory_checks": "轨迹时间窗指标和限位事件筛选",
    "visualization": "离线运动回放 viewer 资产导出",
    "kinematics_conventions": "关节坐标和运动树传播方向的符号约定",
    "kinematics_geometry": "低层后端无关的姿态传播、Jacobian、mobility 和位置求解原语",
    "kinematics_limits": "从关节轨迹检测限位事件",
    "dynamics": "预留动力学命名空间；当前没有公开 API",
}


def _kind(value: Any) -> str:
    if inspect.isfunction(value):
        return "函数"
    if inspect.isclass(value):
        if issubclass(value, enum.Enum):
            return "枚举"
        return "类型"
    if typing.get_origin(value) is not None or getattr(value, "__module__", "") == "typing":
        return "类型别名"
    return "常量"


def _purpose(namespace: str, name: str, value: Any) -> str:
    override = api_docs.PURPOSE_OVERRIDES.get(name)
    if override:
        return re.sub(r"\s+", " ", override).strip()
    if inspect.isclass(value) and issubclass(value, enum.Enum):
        return f"定义 `{namespace}.{name}` 可接受的稳定枚举值。"
    doc = inspect.getdoc(value)
    if doc and not (inspect.isclass(value) and doc.startswith(f"{name}(")):
        return re.sub(r"\s+", " ", doc.splitlines()[0]).strip().rstrip("。.") + "。"
    if inspect.isclass(value):
        patterns = (
            ("Report", "表示结构化诊断或分析报告，保存状态、证据和问题。"),
            ("Result", "表示一次公开操作的结构化结果和可复核证据。"),
            ("Options", "封装对应分析或求解操作的显式选项和容差。"),
            ("State", "表示指定时间的组件、连接点或关节状态。"),
            ("Trajectory", "表示离散采样的运动轨迹及其状态数据。"),
            ("Event", "记录运动或几何检查中发生的一次事件。"),
            ("Request", "描述结果记录或检查所需的对象请求。"),
            ("Driver", "描述 Scenario 中的运动驱动输入。"),
            ("Profile", "描述随时间变化的运动参数曲线。"),
            ("Limit", "描述运动量允许的上下边界。"),
        )
        for suffix, description in patterns:
            if name.endswith(suffix):
                return description
        return f"表示 `{namespace}.{name}` 的公开、不可变数据模型。"
    if name in {"CheckType", "Direction", "RatioMeasurement", "SamplingScope", "MotionStatus", "ConstraintEquationType", "ConstraintEquationUnit", "LimitSide", "LimitEventType", "Severity", "ResultStatus", "IntegrityStatus"}:
        return f"定义 `{name}` 可接受的稳定值。"
    if typing.get_origin(value) is not None:
        return f"定义 `{namespace}.{name}` 使用的公开类型约定。"
    if inspect.isfunction(value):
        return f"执行 `{namespace}.{name}()` 公开操作。"
    return f"表示 `{namespace}.{name}` 的公开、可序列化数据类型。"


def _status(name: str) -> str:
    if name == "verify_transmission_ratio":
        return "兼容保留（弃用）"
    if name in {"apply_assembly_fix", "apply_scenario_fix"}:
        return "已实现类型；当前能力未实现"
    return "已实现"


def generate() -> str:
    rows: list[tuple[str, str, str, str, str]] = []
    namespaces: list[str] = []
    for namespace, info in api_docs.MODULES.items():
        module = importlib.import_module(f"kincheckapi.{namespace}")
        names = api_docs.public_names(namespace, module)
        namespaces.append(namespace)
        for name in names:
            rows.append(
                (
                    f"`kincheckapi.{namespace}.{name}`",
                    namespace,
                    _kind(getattr(module, name)),
                    _purpose(namespace, name, getattr(module, name)),
                    _status(name),
                )
            )
    import kincheckapi

    for name in kincheckapi.__all__:
        value = getattr(kincheckapi, name)
        if inspect.ismodule(value):
            continue
        rows.append(
            (
                f"`kincheckapi.{name}`",
                "kincheckapi (re-export)",
                _kind(value),
                f"根命名空间对 `{name}` 的便利导出；规范模块入口见同名模块行。",
                "已实现",
            )
        )
    for name, kind, purpose, status in CLI_ROWS:
        rows.append((f"`{name}`", "kincheck CLI", kind, purpose, status))

    lines = [
        "# KinCheckAPI Python API 命名空间总表",
        "",
        "> 本文由 `scripts/generate_python_namespace_doc.py` 根据当前各模块的 `__all__` 生成。它是 v0.5.1 的公开 API 总索引；内部模块、以下划线开头的符号和未导出的实现细节不属于本表。",
        "",
        "## 使用边界",
        "",
        "- `kincheckapi.checks` 是所有验收检查的公共命名空间，包含 `check_assembly_integrity()`、干涉、间隙、残差、传动、姿态和轨迹检查。",
        "- `kincheckapi.integrity` 仅是整体性检查的内部实现模块；调用方应从 `kincheckapi.checks` 或根命名空间导入。",
        "- `component_ids=None` 在 `check_assembly_integrity()` 中表示检查整个装配体；多个 Component 通过连接图判断是否属于一个整体。",
        "- 几何连接容差使用米制，运动结果检查必须明确时间窗和实际采样；`partial`、空样本或能力缺失不能判为通过。",
        "",
        "## 命名空间职责",
        "",
        "| Python 命名空间 | 主要职责 |",
        "| --- | --- |",
    ]
    for namespace in namespaces:
        lines.append(f"| `kincheckapi.{namespace}` | {NAMESPACE_PURPOSES.get(namespace, namespace)} |")
    lines.append("| `kincheckapi` | 对常用类型和函数提供稳定的根命名空间便利导出；复杂 API 优先使用其规范模块命名空间。 |")
    lines.extend(
        [
            "| `kincheck CLI` | 所有 harness 共用的环境诊断、模型校验、verifier 执行和 Skill 打包入口。 |",
            "",
            "## API 总表",
            "",
            "| API | 所属命名空间 | 类型 | 用途 | 实现状态 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(f"| {api} | `{namespace}` | {kind} | {purpose} | {status} |" for api, namespace, kind, purpose, status in rows)
    lines.extend(
        [
            "",
            f"总计：{len(rows)} 个公开 Python API/CLI 入口，其中包含模块 API、根命名空间便利导出和 {len(CLI_ROWS)} 个 CLI 入口。",
            "",
            "## 生成与检查",
            "",
            "```bash",
            "uv run python scripts/generate_python_namespace_doc.py",
            "uv run python scripts/generate_skill_api_docs.py --check",
            "uv run python scripts/generate_skill_api_docs_en.py --check",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    output = REPO_ROOT / "design" / "python_namespace.md"
    output.write_text(generate(), encoding="utf-8")
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
