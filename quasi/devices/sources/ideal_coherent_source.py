"""
Ideal Coherent Source Implementation
"""

import numpy as np
from math import factorial

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    coordinate_gui,
    log_action,
    schedule_next_event,
    ensure_output_compute,
)
from quasi.devices.port import Port
from quasi.signals import (
    GenericSignal,
    GenericFloatSignal,
    GenericBoolSignal,
    GenericQuantumSignal,
)

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager

from quasi._math.fock.ops import adagger, a, coherent_state

from photon_weave.state.envelope import Envelope
from photon_weave.operation.fock_operation import FockOperation, FockOperationType


class IdealCoherentSource(GenericDevice): # 继承genericdevice
    """
    COHERENT
    """

    ports = {
        "trigger": Port( # 用于控制光源的开启或出发
            label="trigger",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal, # 布尔类型的信号
            device=None,
        ),
        "alpha": Port( # 表示相干态的幅度：控制光场强度
            label="alpha",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "phi": Port( # 表示相干态的相位：控制光源相位
            label="phi",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.LASER
    gui_tags = ["ideal"]
    gui_name = "Ideal Coherent Photon Source"
    gui_documentation = "ideal_coherent_photon_source.md"

    power_peak = 0
    power_average = 0

    reference = None

    def __init__(self, name=None, frequency=None, time=0, uid=None):
        super().__init__(name=name, uid=uid) # __init__是类的构造函数，用于初始化对象实例
        self.alpha = None # 初始化的幅度和相位都是none
        self.phi = None

    def set_displacement(self, alpha: float, phi: float):
        """
        Sets the signals so that the source correctly displaces the vacuum
        """ # 设置位移函数，把幅度和相位的类型都设置成float，一个专门用于设置相干光源位移的函数
        alpha_sig = GenericFloatSignal() # 创建GenericFloatSignal类型的信号
        alpha_sig.set_float(alpha) # 为这个信号赋值，值是alpha类型是float
        phi_sig = GenericFloatSignal()
        phi_sig.set_float(phi)
        self.register_signal(signal=alpha_sig, port_label="alpha") # 把alpha_sig注册到相应端口
        self.register_signal(signal=phi_sig, port_label="phi")
        phi_sig.set_computed() # 做标记表示信号已经被计算完成（信号准备好被使用了）
        alpha_sig.set_computed()

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs): # 计算相干光源的输出信号
        simulation = Simulation.get_instance()  # 获取simulation实例
        if simulation.simulation_type is SimulationType.FOCK: # 检查实例的类型
            self.simulate_fock() # 如果是Fock类就调用simulate_fock方法进行仿真

    def simulate_fock(self): # 定义Fock态仿真方法
        """
        Fock Simulation
        """
        simulation = Simulation.get_instance() # 获取仿真实例
        backend = simulation.get_backend()  # 从仿真实例中获取后端（后端可能是处理量子态和操作的类）

        # Get the mode manager
        mm = ModeManager() # 定义一个模式管理器，用于管理量子模式
        # Generate new mode
        mode = mm.create_new_mode() # 生成一个新的模式
        # Displacement parameters
        alpha = self.ports["alpha"].signal.contents # 从alpha端口获取幅度
        phi = self.ports["phi"].signal.contents # 从phi端口获取信号内容

        # Initialize photon number state in the mode
        operator = backend.displace(alpha, phi, mm.get_mode_index(mode)) # 在该模式上应用位移操作获得一个操作符，该操作符用于生成相干态
        backend.apply_operator(operator, [mm.get_mode_index(mode)]) # 将上面的位移操作符应用到当前模式，以更新模式的量子态

        self.ports["output"].signal.set_contents(timestamp=0, mode_id=mode) # 在输出端口输出信号内容，包括时间戳和模式id
        self.ports["output"].signal.set_computed() # 标记，表示输出信号已经完成计算

    @coordinate_gui
    @schedule_next_event # 装饰器
    @log_action
    def des(self, time, *args, **kwargs): # 方法用于处理和调度事件。它根据传入的信号决定如何处理相干光源的输出
        signals = kwargs.get("signals") # 提取信号，用于懂kwargs中获得信号字典
        if "alpha" in signals or "phi" in signals: # 如果这个信号腮红有位移
            self._extract_parameters(kwargs) # 调用函数
        if "trigger" in signals: # 如果信号中有trigger信号
            if self.alpha is None:  # 如果不存在，发出异常
                raise Exception("Alpha not provided")
            if signals["trigger"].contents: # 如果存在
                env = Envelope()
                env.fock.dimensions = 10 # 创建envelope对象并设置Fock空间维度为10
                op = FockOperation(FockOperationType.Displace, alpha=self.alpha) # 定义一个操作，类型为displace
                env.apply_operation(op) # 在envelope中应用这个操作
                signal = GenericQuantumSignal() #创建对象signal
                signal.set_contents(content=env) # 设置signal内容为env
                result = [("output", signal, time)] # 获得结果
                return result

    def _extract_parameters(self, kwargs): # 提取参数alpha和phi
        signals = kwargs.get("signals") # 从kwarg中获得signal
        if signals and "alpha" in signals: # 如果signal中有alpha，提取并保存到self alpha中
            self.alpha = signals["alpha"].contents
        if signals and "phi" in signals:
            self.phi = signals["phi"].contents
