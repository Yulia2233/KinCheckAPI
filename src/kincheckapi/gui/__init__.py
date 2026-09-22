"""Native, local KinCheck scenario workbench.

The GUI package is deliberately independent from the read-only web Viewer.  It
owns scenario editing, background execution, result presentation data and
portable verifier-script generation while delegating all numerical work to the
public KinCheckAPI functions.
"""

from .scenario_document import GuiScenarioDocument, GUI_SCENARIO_SCHEMA_VERSION
from .simulation_service import GuiRunResult, GuiSimulationService
from .verification_export import export_verification_bundle, generate_verification_script, zip_verification_bundle

__all__ = [
    "GUI_SCENARIO_SCHEMA_VERSION",
    "GuiScenarioDocument",
    "GuiRunResult",
    "GuiSimulationService",
    "export_verification_bundle",
    "generate_verification_script",
    "zip_verification_bundle",
]
