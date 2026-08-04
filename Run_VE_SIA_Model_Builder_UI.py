"""IESVE Run-button launcher for the native Swiss VE Model Builder UI."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# VE Scripts keeps both the execution launcher and project package alive between
# Run-button executions. Purge both explicitly so a recovery fix is effective
# without forcing the operator to restart VE.
for module_name in tuple(sys.modules):
    if (
        module_name == "Run_VE_SIA_Model_Builder"
        or module_name.startswith("Run_VE_SIA4010_")
        or module_name == "swiss_sia"
        or module_name.startswith("swiss_sia.")
    ):
        del sys.modules[module_name]

# Import the execution launcher first. Its own guard provides a second layer
# before the UI module creates persistent Tk objects.
import Run_VE_SIA4010_Test1_Runtime_Input_Probe as test1_runtime_input_probe
import Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs as test1_runtime_input_qualifier
import Run_VE_SIA_Model_Builder as model_builder
import Run_VE_SIA4010_Evaluate_Active_Case as active_case_evaluator
import Run_VE_SIA4010_APS_Probe as active_aps_probe
import Run_VE_SIA4010_Simulate_Active_Case as active_case_simulator
import Run_VE_SIA4010_Test2A_Profile_Qualification as test2a_profile_qualifier
import Run_VE_SIA4010_Test2A_2E1_Optical_Setter_Qualification as test2a_optical_qualifier
import Run_VE_SIA4010_Test2A_Runtime_Capability_Probe as test2a_runtime_probe
import Run_VE_SIA4010_Test2A_Shading_Setter_Qualification as test2a_shading_qualifier
import Run_VE_SIA4010_Test3_Runtime_Capability_Probe as test3_runtime_probe
import Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe as hvac_plant_runtime_probe

from swiss_sia.reference_model.sia4010.native_ui import launch_native_ui
from swiss_sia.reference_model.ve_api import IesVeGateway


def run():
    """Launch the native interface against the active VE project."""

    gateway = IesVeGateway()
    launch_native_ui(
        project_path=gateway.project_path,
        project_name=gateway.project_name,
        executor=model_builder.run,
        test1_runtime_input_qualifier=test1_runtime_input_qualifier.run,
        repository_root=PROJECT_ROOT,
        test1_runtime_input_probe=test1_runtime_input_probe.run,
        aps_evaluator=active_case_evaluator.run,
        aps_probe=active_aps_probe.run,
        apachesim_runner=active_case_simulator.run,
        test2a_runtime_probe=test2a_runtime_probe.run,
        test2a_profile_qualifier=test2a_profile_qualifier.run,
        test2a_shading_qualifier=test2a_shading_qualifier.run,
        test2a_optical_qualifier=test2a_optical_qualifier.run,
        test3_runtime_probe=test3_runtime_probe.run,
        hvac_plant_runtime_probe=hvac_plant_runtime_probe.run,
    )


if __name__ == "__main__":
    run()
