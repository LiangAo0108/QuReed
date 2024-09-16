"""
Device port definitions
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Type, Literal, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quasi.devices.generic_device import GenericDevice
    from quasi.signals.generic_signal import GenericSignal


@dataclass    # 是一个字典类型
class Port:   # 定义一个port类
    """
    Port Dataclass
    """

    label: str
    direction: Literal["input", "output"]
    signal: Optional["GenericSignal"]
    signal_type: Type["GenericSignal"]
    device: "GenericDevice"
    allow_multiple: bool = False

    def __post_init__(self):  # 创建class后自动调用方法__post_init__
        if None in [self.label, self.direction, self.signal_type]:
            raise PortMissingAttributesException(
                "label, direction and signal_type must be specified"
            )   # 检查label，direction，types是否为none，如果任意一类是none，则引发异常

    def disconnect(self):  # 定义断开连接的方法：断开端口与信号的连接，并清理信号与其他端口的关系
        if self.signal is None:   # 首先检查是否有信号，如果信号是none，则直接返回，这表示没有连接
            return
        signal = self.signal  # 如果信号不是none，则将当前信号保存成self.signal。
        self.signal = None    # 因为要断开连接，所以令信号为none
        ports = signal.ports  # port表示连接到这个signal的所有端口，是个列表
        other_ports = [p for p in ports if p is not self]  # 除了当前端口之外的所有端口
        for p in other_ports:   # 如果端口p是其他端口
            if isinstance(p.signal, list):  # 检查p.signal是不是列表类型
                p.signal.remove(signal)     # 如果是列表，就删除当前信号signal，这表示信号和端口p断开连接
            else:                           # 否则（不是列表），令p.signal等于none，以断开信号连接
                p.signal = None             # 这个方法确保当前端口断开与信号的连接，并且在该信号连接的其他端口中移除该信号。
                


class PortMissingAttributesException(Exception):
    """
    Raised when Attributes are not specified
    """
