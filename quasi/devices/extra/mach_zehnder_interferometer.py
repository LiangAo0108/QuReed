"""
MZI
"""
import traceback

from photon_weave.operation.composite_operation import CompositeOperation, CompositeOperationType
from photon_weave.state.composite_envelope import CompositeEnvelope

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

            signals = kwargs.get("signals", {})

            # get the envelopes
            qin0_signal = signals.get("qin0", None)
            qin1_signal = signals.get("qin1", None)

            if qin0_signal is None:
                env0 = Envelope()
            else:
                env0 = signals["qin0"].contents


            if qin1_signal is None:
                env1 = Envelope()
            else:
                env1 = signals["qin1"].contents

            print(f"qin0_signal: {qin0_signal}, qin1_signal: {qin1_signal}")
            print(f"env0: {env0}, env1: {env1}")



            if (qin0_signal is None) and (qin1_signal is None):
                print("MZI has no input")
                logger.info("MZI no input here")
                return

            ce = CompositeEnvelope(env0,env1)
            ce.combine(env0.fock, env1.fock)
            print (f"ce.states[0]:{ce.states[0]}")

            # create operator for beam splitter and phase shifter
            fo_beam_splitter = CompositeOperation(CompositeOperationType.NonPolarizingBeamSplit)
            fo_phase_shifter = FockOperation(FockOperationType.PhaseShift, phi=self.phase_shift)
            # apply the beam splitter
            ce.apply_operation(fo_beam_splitter, env0, env1)
            print(f"ce.states[0] after first beam splitter: {ce.states[0]}")
            # apply the phase shifter
            ce.apply_operation(fo_phase_shifter,env1)
            # apply the beam splitter twice
            ce.apply_operation(fo_beam_splitter, env0, env1)


            # create new quantum signals
            qout0_signal = GenericQuantumSignal()
            qout1_signal = GenericQuantumSignal()

            # set the modified envelope to the content of output signal
            qout0_signal.set_contents(env0)
            qout1_signal.set_contents(env1)
            # return to the result
            result = [("qout0", qout0_signal, time),("qout1", qout1_signal, time)]
            return result

        except Exception as e:
            logger.error("Error", exc_info=True)






