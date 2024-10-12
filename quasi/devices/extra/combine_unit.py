from photon_weave.operation.composite_operation import CompositeOperation, CompositeOperationType
from photon_weave.state.composite_envelope import CompositeEnvelope

from examples.quantum_message_transmission import signals
#from scipy.special import result
from quasi.devices import (GenericDevice,
                           schedule_next_event,
                           log_action,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericBoolSignal,
                           GenericQuantumSignal, GenericFloatSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager
from quasi.extra.logging import Loggers, get_custom_logger
from photon_weave.state.envelope import Envelope
from photon_weave.operation.fock_operation import FockOperationType, FockOperation

from quasi.devices.extra.mach_zehnder_interferometer import MachZehnderInterferometer

logger = get_custom_logger(Loggers.Devices)

class CombineUnit(GenericDevice):

    ports = {
        "input0": Port(
            label="input0",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "input1": Port(
            label="input1",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "input2": Port(
            label="input2",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "input3": Port(
            label="input3",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "output1": Port(
            label="output1",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "output2": Port(
            label="output2",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "output3": Port(
            label="output3",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "output0": Port(
            label="output0",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.PHASE_SHIFT
    gui_tags = ["ideal"]
    gui_name = "4 modes"
    gui_documentation = "4 modes optical processor.md"

    power_average = 0
    power_peak = 0
    reference = None

    def __init__(self, name=None, uid=None): # initialize
        super().__init__(name=name, uid=uid)

        # 5 unit cells
        self.unit_cell_1 = MachZehnderInterferometer()
        self.unit_cell_2 = MachZehnderInterferometer()
        self.unit_cell_3 = MachZehnderInterferometer()
        self.unit_cell_4 = MachZehnderInterferometer()
        self.unit_cell_5 = MachZehnderInterferometer()




    @wait_input_compute
    def compute_outputs(self,  *args, **kwargs):
        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=self.ports["input"].signal.mode_id
        )

    #@log_error
    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        try:
            signals = kwargs.get("signals", {})

            # get the envelopes and apply the external phase shifter on input
            input_signals = [signals.get(f"input_{i}", None) for i in range(4)]
            for i in range(4):
                if input_signals[i] is not None:
                    env = input_signals[i].contents

                else:
                    env = Envelope()

            print(f"input_signal: {input_signals}")
            print(f"env: {env}")

            # connect unit cell 1 and unit cell 2 with inputs
            unit_cell_1_output = self.unit_cell_1.des(qin0=input_signals[0], qin1=input_signals[1], signals=signals)
            unit_cell_2_output = self.unit_cell_2.des(qin0=input_signals[2], qin1=input_signals[3], signals=signals)

            # connect unit cell 3 from cell 1 and cell 2
            unit_cell_3_output = self.unit_cell_3.des(qin0=unit_cell_1_output[0][1], qin1=unit_cell_2_output[0][1],
                                                  signals=signals)

            # connect unit cell 4 from cell 1 and cell 3
            unit_cell_4_output = self.unit_cell_4.des(qin0=unit_cell_1_output[1][1], qin1=unit_cell_3_output[0][1],
                                                  signals=signals)

            # connect unit cell 5 from cell 2 and cell 3
            unit_cell_5_output = self.unit_cell_5.des(qin0=unit_cell_2_output[1][1], qin1=unit_cell_3_output[1][1],
                                                  signals=signals)


            # define the output of processor:
            #env_output_0 = unit_cell_4_output[0][1].contents
            #env_output_1 = unit_cell_5_output[0][1].contents
            #env_output_2 = unit_cell_4_output[1][1].contents
            #env_output_3 = unit_cell_5_output[1][1].contents


            result = [
                ("output_0", unit_cell_4_output[0][1], time),
                ("output_1", unit_cell_4_output[1][1], time),
                ("output_2", unit_cell_5_output[0][1], time),
                ("output_3", unit_cell_5_output[1][1], time)
            ]
            return result

        except Exception as e:
            logger.error("Error in FourModesStructure", exc_info=True)



