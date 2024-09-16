"""
Ideal Single Photon Source implementation
"""
import numpy as np

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           schedule_next_event,
                           log_action,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericBoolSignal,
                           GenericIntSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager
from quasi.experiment import Experiment
from quasi.extra.logging import Loggers, get_custom_logger
from quasi.backend.envelope_backend import EnvelopeBackend
from photon_weave.state.envelope import Envelope
from photon_weave.operation.fock_operation import(
    FockOperation, FockOperationType
)

logger = get_custom_logger(Loggers.Devices)


class IdealNPhotonSource(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "trigger": Port(
            label="trigger",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None),
        "photon_num": Port(
            label="photon_num",
            direction="input",
            signal=None,
            signal_type=GenericIntSignal,
            device=None),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.N_PHOTON_SOURCE
    gui_tags = ["ideal"]
    gui_name = "Ideal N Photon Source"
    gui_documentation = "ideal_n_photon_source.md"

    power_peak = 0
    power_average = 0
    reference = None

    def __init__(self, name=None, time=0, uid=None):
        super().__init__(name=name, uid=uid)
        self.photon_num = None

    def set_photon_num(self, photon_num: int): # 定义用于设置光子数的函数
        """
        Set the number of photons the source should emit in a pulse
        """
        photon_num_sig = GenericIntSignal() # 创建信号photon_num_sig，类型为GenericIntSignal
        photon_num_sig.set_int(photon_num) # 设置信号内容为光子数
        self.register_signal(signal=photon_num_sig, port_label="photon_num") # 把信号注册到端口
        photon_num_sig.set_computed() # 做标记，表示信号已经被处理完了，可以被使用了
    

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs): # 用于计算输出的函数
        simulation = Simulation.get_instance()  # 设置仿真实例
        if simulation.simulation_type is SimulationType.FOCK: # 确定仿真类型是否是Fock类型
            self.simulate_fock() # 如果是Fock类就调用simulate_fock方法进行仿真

    def simulate_fock(self): # 定义simulate_fock方法
        """
        Fock Simulation
        """
        simulation = Simulation.get_instance() # 获取仿真实例
        backend = simulation.get_backend() # 从仿真实例中获取后端（后端可能是处理量子态和操作的类）

        # Get the mode manager
        mm = ModeManager()
        # Generate new mode
        mode = mm.create_new_mode()
        # How many photons should be created
        photon_num = self.ports["photon_num"].signal.contents  # 从photon_num端口获取内容
        
        # Initialize photon number state in the mode 在模式中初始化光子数状态
        backend.initialize_number_state(photon_num, [mm.get_mode_index(mode)])

        logger.info(  # 在日志中记录什么mode被分给了什么port
            "Source - %s - assisning mode %s to signal on port %s",
            self.name, mm.get_mode_index(mode),
            self.ports["output"].label)
        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=mode) # 获取输出端口的内容
        self.ports["output"].signal.set_computed() # 把输出端标记为已计算

    def set_photon_num(self, photon_num: int):
        """
        Set the number of photons the source should emit in a pulse
        """
        self.photon_num = photon_num

    @coordinate_gui
    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        if "photon_num" in kwargs["signals"]: # 检查 kwargs["signals"] 中是否存在 "photon_num" 信号
            # 如果存在photon_num，则从信号中提取光子数值，并将其转换为浮点数，然后通过 self.set_photon_num 方法存储在类实例中
            self.set_photon_num(float(kwargs["signals"]["photon_num"].contents))
        elif "trigger" in kwargs["signals"] and self.photon_num is not None: # 如果 kwargs["signals"]中包含trigger信号，并且self.photon_num已经被设置
            n = int(self.photon_num) # 将self.photon_num转化为整数，表示光子数
            # Creating new envelopt
            env = Envelope()  # 创建一个新的变量envelope，对象env
            # Applying operation：创建一个 FockOperation 对象 op，指定操作类型为 Creation（创建光子），并且应用 n 次（即生成 n 光子的态）
            op = FockOperation(FockOperationType.Creation, apply_count=n)
            env.apply_operation(op) # 将该操作应用到 env 上，表示在这个量子态中生成 n 光子
            # Creating output
            signal = GenericQuantumSignal()
            signal.set_contents(content=env) # 封装的量子态 env 设置为信号的内容
            result = [("output", signal, time)]
            return result
        else:
            raise Exception("Unknown Photon Num")
