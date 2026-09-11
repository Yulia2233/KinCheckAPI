# `CheckSpec`

## API 定义

```python
@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    check_type: str
    parameters: Mapping[str, Any]
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import CheckSpec
```

## 用途

表示 `CheckSpec` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `check_id` | `str` | 必填 | 调用方提供的稳定检查 ID，用于结果追溯。 |
| `check_type` | `str` | 必填 | `check_type` 的公开输入或数据字段。 |
| `parameters` | `Mapping[str, Any]` | default_factory | 该检查类型的显式参数；不得依赖未记录的隐式默认验收标准。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 检查必须对应明确的对象、时间窗、期望值、阈值和单位。
- 检查对象为空、证据为空或 MotionResult 不完整时不得通过。
- `CheckReport.passed` 是最终布尔结论；同时保留 evidence、issues 和 metadata。
- 装配体整体性检查支持任意数量的 Component；`component_ids=None` 检查整个装配体。
- 机械、容纳/导向和几何连接共同形成连接图；几何连接必须记录米制容差。

## 相关文档

- [`验收检查`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
