"""使用 KinCheckAPI 验证 ex2 二级行星齿轮装配体的总减速比。

运行方式：
    uv run python examples/compact_two_stage_planetary_reducer/kincheckapi/verify.py

这个示例只调用 KinCheckAPI 的公开模块。调用者不需要创建或操作任何
底层求解器对象。
"""

from pathlib import Path

from kincheckapi import cadir, checks, kinematics, scenario


CASE_DIR = Path(__file__).resolve().parents[1]

# 这些 ID 来自 CADIR MJCF mapping 中的显式装配关系，不通过零件名称猜测。
# ex2 的输入是输入轴转动关节，输出是第二级行星架转动关节。
INPUT_JOINT_ID = "input_shaft_revolute"
OUTPUT_JOINT_ID = "stage2_carrier_revolute"

# 第一级设计减速比为 5:1，第二级为 4:1，因此总减速比为 20:1。
EXPECTED_RATIO = 20.0


def evidence_value(*, report, key: str):
    """Read one named measurement from a generic CheckReport."""

    return next((item.actual for item in report.evidence if item.key == key), None)


def main() -> None:
    # 1. 读取 CADIR MJCF、mapping 和网格目录。
    mjcf_root = CASE_DIR / "model_before"
    converted = cadir.convert_mjcf(
        xml_path=mjcf_root / "scene.xml",
        mapping_path=mjcf_root / "scene.mapping.json",
        asset_root=mjcf_root,
    )

    # 2. 使用 CADIR MJCF + mapping 得到 KinCheckAPI 的 AssemblyModel。
    assembly = converted.assembly

    # 3. 创建绑定到该装配体的工况。
    # Scenario 是不可变对象，因此每个配置函数都会返回一个新的 Scenario。
    condition = scenario.create_scenario(scenario_id="verify.ex2", assembly=assembly)

    # 4. 对输入轴施加 8 rad/s 的恒速驱动，持续 1 秒。
    # 驱动通过公开 Joint ID 指定，不需要提供行星齿轮专用定义对象。
    condition = scenario.add_joint_speed_driver(
        scenario=condition,
        joint_id=INPUT_JOINT_ID,
        speed_rad_s_or_m_s=8.0,
        start_time_s=0.0,
        end_time_s=1.0,
    )

    # 5. 设置总仿真时间和结果采样周期。
    # 0.02 s 的采样周期会产生足够的速度样本用于稳态减速比验证。
    condition = scenario.set_run_duration(scenario=condition, duration_s=1.0)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.02)

    # 6. 显式请求输入和输出关节轨迹。
    # MotionResult 将使用相同的稳定 Joint ID 返回位置、速度和加速度。
    condition = scenario.request_joint_result(
        scenario=condition, joint_id=INPUT_JOINT_ID
    )
    condition = scenario.request_joint_result(
        scenario=condition, joint_id=OUTPUT_JOINT_ID
    )

    # 7. 执行工况。返回值是后端无关的 MotionResult。
    # 若工况、装配关系或求解过程失败，此处会抛出结构化 KinCheckAPI 异常。
    motion = kinematics.solve_motion(scenario=condition)

    # 8. 从实际运动时间序列测量 input_speed / output_speed。
    # 从 0.1 s 开始统计，避免启动瞬间输出速度接近零造成比值放大。
    # expected_direction="same" 表示输入轴与第二级行星架应同向旋转。
    check = checks.check_transmission_ratio(
        motion_result=motion,
        input_joint_id=INPUT_JOINT_ID,
        output_joint_id=OUTPUT_JOINT_ID,
        expected_ratio=EXPECTED_RATIO,
        expected_direction="same",
        start_time_s=0.1,
        end_time_s=1.0,
        relative_tolerance=1e-3,
    )

    # 检查失败保留原报告，并用同一 Agent 正文终止严格流程。
    check.raise_if_failed()

    # 正常情况下应输出 measured=20.000000。
    measured_ratio = evidence_value(report=check, key="median_ratio")
    print(
        f"ex2: measured={measured_ratio:.6f}, "
        f"expected={EXPECTED_RATIO:.6f}, status={motion.status}"
    )


if __name__ == "__main__":
    main()
