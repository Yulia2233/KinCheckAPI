# Prompt → CAD → 运动学仿真 Benchmark

本目录定义一个可重复的 Agent 评测：Agent 只接收自然语言建模 Prompt，使用 SimpleCADAPI/CADIR 生成参数化装配，最终只交付 `.scadpkg`。Prompt 必须把 verifier-facing 的所有名称和材料单位写死；固定的 KinCheckAPI verifier 由评测端私下从 package 导出输入并运行运动学、闭环、限位、干涉、间隙和连接性检查；Agent 不看到也不修改 verifier。评分依据是评测端结构化结果，不依据图片、解释文字或 Agent 自己写的报告。

- [规范](spec.md)：输入、命名、几何表格、工况文本、产物、固定 verifier 和评分门槛。
- [Prompt 模板](prompt-template.md)：可复制的任务模板，第一部分就是“组件名—命名—几何描述”三列表格。
- [四连杆示例 Prompt](guided_four_bar/prompt.md)：与现有 `examples/guided_four_bar_actuator` 验证器契约一致的完整案例；不修改现有 example。
- [验证脚本规范](verifier-spec.md)：固定入口、JSON/exit code、来源指纹、独立证据、负例和 hard-pass 规则。
- [四连杆 benchmark](guided_four_bar/README.md)：目录根部配对放置 `prompt.md` 和原样 `verify.py`。
- [XYZ 直驱龙门 benchmark](xyz_pick_place_gantry/README.md)：目录根部配对放置三轴直驱 `prompt.md` 和动力学 `verify.py`。
- [Package adapter](adapter.py)：输入 `.scadpkg` 和 verify 脚本路径，准备仿真目录、补齐临时 collision meshes，执行 verifier 并输出 JSON 证据。

当前四连杆的评测连接链是：Agent Prompt → SimpleCADAPI/CADIR `.scadpkg` → 评测端导出 MJCF、mapping、meshes 和 collision meshes → `kincheckapi.cadir.convert_mjcf()` → 私有固定 verifier。现有 `examples/guided_four_bar_actuator` 只作为命名、几何和验证契约的参考，不被 Prompt Agent 修改。

Adapter 示例：

```bash
python benchmark/adapter.py \
  /path/to/guided_four_bar_actuator.scadpkg \
  /path/to/verification/verify.py \
  --work-dir /tmp/kincheck-benchmark
```

输出 JSON 会包含 `.scadpkg` 路径、verify 脚本路径、准备后的 model 目录、执行命令、return code、stdout 和 stderr。adapter 会在本进程内把 `g/cm3`、`kg/mm3` 等密度单位归一化为 `kg/m3`，不修改原始 `.scadpkg`，并在 `density_normalization` 字段记录换算。
