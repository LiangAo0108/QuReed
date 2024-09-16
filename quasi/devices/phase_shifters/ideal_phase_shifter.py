"""
Ideal Phase Shifter
"""

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    coordinate_gui,
    log_action,
    schedule_next_event,
    ensure_output_compute,
)
from quasi.devices.port import Port
from quasi.signals import GenericSignal, GenericFloatSignal, GenericQuantumSignal
from quasi.extra.logging import Loggers, get_custom_logger
from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager

from photon_weave.operation.fock_operation import FockOperationType, FockOperation

logger = get_custom_logger(Loggers.Devices)  # 定义一个日志记录器，记录设备操作的信息


class IdealPhaseShifter(GenericDevice):  # 定义一个移相器，继承自GenericDevice
    """
    Implements Ideal Phase Shifter
    """
# 定义移相器的三个端口，input，output和theta。port是字典，key是theta，input和output
    ports = {
        "theta": Port(  # 用于指定相移量,theta是端口的名字
            label="theta",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
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
# 移相器会根据theta端口输入的相移量信号，对input端口接受的量子信号进行相位调制，将调制后的信号从output中输出
    gui_icon = icon_list.PHASE_SHIFT
    gui_tags = ["ideal"]
    gui_name = "Ideal Phase Shifter"
    gui_documentation = "ideal_phase_shifter.md"

    power_peak = 0
    power_average = 0
    reference = None

    def __init__(self, name=None, time=0, uid=None):
        super().__init__(name=name, uid=uid)  # 调用父类的初始化方法
        self.theta = 0   # 表示初始相移量为0

    def set_theta(self, theta):  # 目的：设置相移量theta
        """
        Sets the phi for the phase shifter
        """
        theta_sig = GenericFloatSignal()  # 设置用于表示相移量的信号，创建一个GenericFloatSignal实例
        theta_sig.set_float(theta)  # 将theta的值转换成theta_sig的浮点值
        self.register_signal(signal=theta_sig, port_label="theta")  # 将theta_sig信号注册到设备的theta端口，表明该端口现在有了新的信号输入
        theta_sig.set_computed()  # 将theta_sig设置成“已计算”

    @ensure_output_compute  # 确保输出在所有输入都已经计算之后进行计算
    @coordinate_gui  # 协调GUI操作
    @wait_input_compute  # 确保在计算输出之前，所有输入信号已经计算完毕
    def compute_outputs(self, *args, **kwargs):  # 目的：计算移相器的输出信号
        simulation = Simulation.get_instance()  # 获取当前仿真实例
        if simulation.simulation_type is SimulationType.FOCK:  # 如果仿真的类型是fock
            self.simulate_fock()  # 则调用fuck方法进行仿真计算

    def simulate_fock(self):  # 模拟了一个相移器在 Fock 状态下的行为
        """
        Fock Simulation
        """
        logger.info("Beam Splitter - %s - executing", self.name)  # 记录日志，表明移相器开始执行
        simulation = Simulation.get_instance()  # 获取当前仿真实例simulation
        backend = simulation.get_backend()  # 从仿真实例中获取后端 backend，用于执行实际的量子操作

        # Get the mode manager
        mm = ModeManager()  # 创建模式管理器mm，用于管理光子模式
        # Generate new mode
        theta = self.ports["theta"].signal.contents  # 获取相移量theta的内容
        mode = self.ports["input"].signal.mode_id  # 获取input的模式id
        logger.info(
            "Phase Shifter - %s - received mode %s from signal on port %s",
            self.name,
            mm.get_mode_index(mode),
            self.ports["output"].label,
        )  # 记录接受到的模式信息，表明相移器接收到特定模式 mode 的信号

        # Initialize photon number state in the mode
        operator = backend.phase_shift(theta, mm.get_mode_index(mode))  # 使用后端创建相移操作符operator，该操作符将应用于指定模式 mode
        backend.apply_operator(operator, [mm.get_mode_index(mode)])  # 将操作符 operator 应用于指定模式

        logger.info(
            "Phase Shifter - %s - assisning mode %s to signal on port %s",
            self.name,
            mm.get_mode_index(mode),
            self.ports["output"].label,
        )  # 记录日志，表明相移器将模式 mode 分配给 output 端口的信号

        self.ports["output"].signal.set_contents(timestamp=0, mode_id=mode)  # 将模式 mode 和时间戳 0 设为 output 端口信号的内容
        self.ports["output"].signal.set_computed()  # 将 output 端口信号标记为已计算，表示该信号已经准备好用于后续处理

    @log_action  # 记录方法被调用的时间，并生成一条日志，表明方法正在执行
    @schedule_next_event  # 它会处理方法的返回结果，并为连接的设备和端口调度新事件
    def des(self, time=None, *args, **kwargs):  # 定义des方法用于处理移相器的输入信号
        if "theta" in kwargs.get("signals"):  # 检查 kwargs 中是否包含 signals，并且 signals 是否包含键 "theta"
            self.theta = kwargs["signals"]["theta"].contents  # 如果存在 "theta" 信号，将其内容赋值给 self.theta，表示相移器的相移量
        if "input" in kwargs.get("signals"):  # 检查 kwargs 中是否包含 signals，并且 signals 是否包含键 "input"
            env = kwargs["signals"]["input"].contents  # 如果存在input信号，则获取input的内容，记做env
            fo = FockOperation(FockOperationType.PhaseShift, phi=self.theta)  # 创建一个 Fock 操作 fo，类型为 PhaseShift，并设置相移量 phi 为 self.theta
            env.apply_operation(fo)  # 将相移操作 fo 应用于输入信号的包络 env
            signal = GenericQuantumSignal()  # 创建一个新的量子信号 signal
            signal.set_contents(env)  # 将修改后的包络 env 设置为该信号的内容。
            result = [("output", signal, time)]  # 构造结果列表 result，包含一个三元组 ("output", signal, time)，表示输出端口的信号和时间。
            return result  # 返回结果列表 result，用于调度下一个事件
