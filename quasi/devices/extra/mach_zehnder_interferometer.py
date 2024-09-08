"""
Unit Cell
"""
import traceback
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
# import beam splitter nad phase shifter
from quasi.devices.beam_splitters import IdealBeamSplitter
from quasi.devices.phase_shifters import IdealPhaseShifter

logger = get_custom_logger(Loggers.Devices)

# inherit from ideal beam splitter and create apply function to use
class MZI_BeamSplitter(IdealBeamSplitter):
    def apply(self, signal_in0, signal_in1):
        output0 = super().des(signal_in0)
        output1 = super().des(signal_in1)
        return output0, output1

# inherit from ideal phase shifter and create apply function
class MZI_PhaseShifter(IdealPhaseShifter):
    def apply(self, singal_shift):
        output_shift = super().des(singal_shift)
        return output_shift

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
        self.qin0 = 0
        self.qin1 = 0
        self.beam_splitter = MZI_BeamSplitter()
        self.phase_shifter = MZI_PhaseShifter()


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

        signals = kwargs.get("signals")

        # check if input signal is existing
        if "qin0" in signals:
            self.qin0 = kwargs["signals"]["qin0"].contents
        else:
            logger.error("error: qin0 signal is missing or none")
            self.qin0 = 0
        if "qin1" in signals:
            #in_qin1 = signals["qin1"]
            #env1 = kwargs["signals"]["qin1"].contents
            self.qin1 = kwargs["signals"]["qin1"].contents
        else:
            logger.error("error: qin1 signal is missing or none")
            self.qin1 = 0

        # check if phase_shift signal is existing
        if "phase_shift" in kwargs.get("signals"):
            self.phase_shift = kwargs["signals"]["phase_shift"].contents
        else:
            logger.error("error: phase shift signal is missing or none")
            #self.phase_shift = 0
            raise ValueError("phase_shift signal is missing.")


        # through the first beam splitter, the output named bs_output
        bs_output0, bs_output1 = self.beam_splitter.apply(self.qin0, self.qin1)

        # apply phase shifter on bs_output1
        output_shift = self.phase_shifter.apply(bs_output1)

        # through the second beam splitter
        qout0,qout1 = self.beam_splitter.apply(self.qin0, output_shift)

        # output signal
        self.ports["qout0"].signal = GenericQuantumSignal(qout0)
        output_signal_0 = GenericQuantumSignal(qout0)  # 输出端口0的信号
        output_signal_1 = GenericQuantumSignal(qout1)  # 输出端口1的信号

        try:
            result = [("qout0", output_signal_0, time), ("qout1", output_signal_1, time)]
            return result

        # Write the functionality here

        except Exception as e:
            logger.error("Error", exc_info=True)





