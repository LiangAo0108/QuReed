"""
MZI
"""
import traceback

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



logger = get_custom_logger(Loggers.Devices)

class MachZehnderInterferometer(GenericDevice):
    """
    Implements Mach Zehnder Interferometer
    """
    ports = {
        "qin0": Port(
            label="qin0",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "qin1": Port(
            label="qin1",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "phase_shift": Port(
            label="phase_shift",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None),
        "qout0": Port(
            label="qout0",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "qout1": Port(
            label="qout1",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None)
    }

    # Gui Configuration
    gui_icon = icon_list.PHASE_SHIFT
    gui_tags = ["ideal"]
    gui_name = "Mach Zehnder Interferometer"
    gui_documentation = "mach_zehnder_interferometer.md"

    power_average = 0
    power_peak = 0
    reference = None

    def __init__(self, name=None, uid=None): # initialize MZI including device name and unique identifier
        super().__init__(name=name, uid=uid)
        self.phase_shift = 0
        self.qin0 = GenericQuantumSignal()
        self.qin1 = GenericQuantumSignal()

    @wait_input_compute
    def compute_outputs(self,  *args, **kwargs):
        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=self.ports["input"].signal.mode_id
        )

    #@log_error
    @log_action
    @schedule_next_event

    def des(self, time=None, *args, **kwargs):
        try:
            if "phase_shift" in kwargs.get("signals"):
                self.phase_shift = kwargs["signals"]["phase_shift"].contents

            signals = kwargs.get("signals",{})

            #if "qin0" in signals and "qin1" in signals:
                #env_qin0 = kwargs["signals"]["qin0"].contents
                #env_qin1 = kwargs["signals"]["qin1"].contents
            qin0_signal = signals.get("qin0", None)
            qin1_signal = signals.get("qin1", None)


            if "qin0" in signals and "qin1" in signals:
                # check if input signal is none. if no input then create new envelope
                if qin0_signal is None:
                    env_qin0 = NewEnvelope()  # create
                else:
                    env_qin0 = kwargs["signals"]["qin0"].contents

                if qin1_signal is None:
                    env_qin1 = NewEnvelope()
                else:
                    # env_qin1 = env_qin1.contents
                    env_qin1 = kwargs["signals"]["qin0"].contents

            if (qin0_signal is None or qin0_signal.contents is None) and (qin1_signal is None or qin1_signal.contents is None):
                print("MZI has no input")
                return

            # create operator for beam splitter and phase shifter
            fo_beam_splitter = FockOperation(FockOperationType.BeamSplitter)
            fo_phase_shifter = FockOperation(FockOperationType.PhaseShift, phi=self.phase_shift)

            # apply the beam splitter
            env_qin0.apply_operation(fo_beam_splitter)
            env_qin1.apply_operation(fo_beam_splitter)

            # apply the phase shifter
            env_qin0.apply_operation(fo_phase_shifter)
            env_qin1.apply_operation(fo_phase_shifter)

            # create new quantum signals
            signal_qout0 = GenericQuantumSignal()
            signal_qout1 = GenericQuantumSignal()

            # set the modified envelope to the content of output signal
            signal_qout0.set_contents(env_qin0)
            signal_qout1.set_contents(env_qin1)


            # return to the result
            result = [("qout0", signal_qout0, time),("qout1", signal_qout1, time)]
            return result

        except Exception as e:
            logger.error("Error", exc_info=True)

class NewEnvelope:
    def __init__(self, initial_state=None):

        if initial_state is None:
            self.state = 0
        else:
            self.state = initial_state





