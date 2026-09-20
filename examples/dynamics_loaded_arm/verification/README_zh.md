# E01 验证

`verify.py` 与 CAD 建模源独立，要求明确的包成员并返回 `passed`、`status`、发生什么、原因、修复建议、对象、单位、证据和来源哈希。`checks.py` 负责转换、静力姿态、全部 BREP 实体配对、独立力矩和额定值检查；`archive_results.py` 写出 `.kincheck`、`physics.json`、viewer 证据、manifest 和往返 JSON；`negative_controls.py` 覆盖缺密度、坏单位、payload 重复、支承缺失、自由轴、反力不唯一、额定值失败、密度篡改、帧破坏、覆盖缺失和护罩侵入。

`passed` 只表示请求命题已被证据建立；额定值失败或反力不确定会保留在结果中。后续版本能力不包含在本版声明内。
