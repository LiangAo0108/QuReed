"""
"""

import numpy as np

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    log_action,
    schedule_next_event,
    coordinate_gui,
    ensure_output_compute,
)
from quasi.devices.port import Port
from quasi.signals import (
    GenericSignal,
    GenericBoolSignal,
    GenericIntSignal,
    GenericQuantumSignal,
)

from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager

from quasi._math.fock.ops import adagger, a


class IdealDetector(GenericDevice): # 继承了genericdevice的类
    """
    Implements Ideal Single Photon Source 理想的单光子探测器
    """

    ports = { # 定义端口
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
            signal_type=GenericIntSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.DETECTOR
    gui_tags = ["ideal"]
    gui_name = "Ideal Detector"
    gui_documentation = "detector.md"

    power_peak = 0
    power_average = 0

    reference = None

    @ensure_output_compute
    @coordinate_gui # 协调gui更新的装饰器
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs): # 计算输出，但没有实现逻辑
        pass # 仅通过装饰器标记功能

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs): # des方法，用于处理和模拟探测器的事件
        env = kwargs["signals"]["input"].contents # 通过kwarg获取输入信号环境env
        ce = env.composite_envelope # 获取复合信号的包络（一个复杂的量子信号的表示）
        print(ce.states[0][0]) # 打印包络的第一个状态
        outcome = ce.measure(env) # 测量输入信号env，结果存在outcome中
        signal = GenericIntSignal() # 创建输出信号，一个整数的信号对象
        print(outcome)
        signal.set_int(outcome[0]) # 将测量结果的第一个值设为整数信号

        results = [("output", signal, time)] # 返回结果，结果包括三项内容
        return results
