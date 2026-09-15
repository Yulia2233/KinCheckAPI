"""Stable structured failure fixture used by regression tests."""
import json
from kincheckapi.diagnostics import Evidence, SimIssue, ValidationResult, format_result_for_agent

result = ValidationResult(issues=(SimIssue(code="KINCHECK-TEST-EMPTY-COMPONENT-PAIRS", severity="error", stage="assembly.integrity", message="No geometric component pairs were supplied.", evidence=(Evidence(key="component_pairs", actual=(), expected="at least one pair"),), suggested_actions=("Declare explicit component pairs.",)),), operation="check_assembly_integrity")
payload = {"status": "validation_failed", "result": result.to_dict(), "agent_output": format_result_for_agent(result)}
print(json.dumps(payload, sort_keys=True))
