"""
Unit Cell
"""

from quasi.devices import (GenericDevice,
                           schedule_next_event,
                           log_action,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericBoolSignal,
                           GenericQuantumSignal, GenericComplexSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager
from quasi.extra.logging import Loggers, get_custom_logger
from photon_weave.state.envelope import Envelope

logger = get_custom_logger(Loggers.Devices)

class MachZehnderInterferometer(GenericDevice):
    """
    Implements Unit Cell
    """
    ports = {
        "qin0": Port(label="qin0", direction="input", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "qin1": Port(label="qin1", direction="input", signal=None,
                     signal_type=GenericQuantumSignal, device=None),
        "phase_shift": Port(label="phase_shift", direction="input", signal=None,
                  signal_type=GenericComplexSignal, device=None),
        "qout0": Port(label="qout0", direction="output", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "qout1": Port(label="qout1", direction="output", signal=None,
                      signal_type=GenericQuantumSignal, device=None)
    }

    # Gui Configuration
    gui_icon = icon_list.PHASE_SHIFT
    gui_tags = ["ideal"]
    gui_name = "Mach Zehnder Interferometer"
    gui_documentation = "mach_zehnder_interferometer.md"

    power_average = 0
    power_peak = 0
    reference = None


    @wait_input_compute
    def compute_outputs(self,  *args, **kwargs):
        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=self.ports["input"].signal.mode_id
        )


    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        """
        It is a Mach Zehnder Interferometer

        """
        env = kwargs["signals"]["input"].signal.contents
        signal = GenericQuantumSignal()
        signal.set_contents(content=env)
        result = [("output", signal, time+1)]
        return results
