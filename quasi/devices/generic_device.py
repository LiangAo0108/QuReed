"""
Generic Device definition
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Type
from copy import deepcopy
import functools

from quasi.simulation import Simulation, DeviceInformation
from quasi.extra import Loggers, get_custom_logger
from quasi.signals.generic_signal import GenericSignal
from quasi.devices.port import Port
from quasi.simulation import ModeManager


def log_action(method):  # log action装饰器：用于记录方法的执行时间和相关信息，method是被装饰的方法
    @functools.wraps(method)  # *args 和 **kwargs 用于接受可变数量的位置参数和关键字参数。
    def wrapper(self, time, *args, **kwargs):  # 定义包装函数wrapper，接受与被装饰方法相同的参数
        # Convert mpf to float for formatting
        l = get_custom_logger(Loggers.Devices)  # 获取一个自定义日志记录器 l，专门用于记录设备相关的信息。Loggers.Devices 是日志记录器的标识符。
        time_as_float = float(time)  # 将时间转换成浮点数
        # Correctly format the string before passing to l.info
        if self.name is not None:  # 如果设备有名字
            formatted_message = "[{:-3e}s] *{}* ({}) is computing".format(
                time_as_float, self.name, self.__class__.__name__
            )  # 格式化日志信息formatted_message，包括时间、设备名称和类名。
        else:  # 如果设备没有名字
            formatted_message = "[{:.3e}s] {} is computing".format(
                time_as_float, self.__class__.__name__
            )  # 格式化日志信息仅包括时间和类名。

        # Now, pass the formatted_message to the log（将日志信息传递给log）
        l.info(formatted_message)  # 将格式化后的日志信息 formatted_message 记录到日志中。
        return method(self, time, *args, **kwargs)  # 调用被装饰的方法method，传递self，time和args，kwargs

    return wrapper  # 返回包装函数wrapper，使其能够代替原始方法执行并添加日志记录功能。


def wait_input_compute(method):  # wait_input_compute 是一个装饰器
    """
    作用：Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    """

    @functools.wraps(method)  # 用于在执行方法前检查设备的输入端口
    def wrapper(self, *args, **kwargs):  # wrapper 函数是实际的包装函数，接受与被装饰方法相同的参数。
        for port in self.ports.keys():  # 遍历设备的所有端口
            port = self.ports[port]     # 将每个键对应的端口对象赋值给 port 变量。
            if port.direction == "input":  # 如果端口方向是 "input" 并且有信号连接
                if port.signal is not None:
                    port.signal.wait_till_compute()  # 为这个端口调用函数wait_till_compute，确保该信号已经计算完成
        return method(self, *args, **kwargs)  # 调用被装饰的方法

    return wrapper  # 返回该方法的结果


def ensure_output_compute(method):  # 目的是确保计算output之前，input已经计算完毕
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    TODO: write the logic
    """

    @functools.wraps(method)  # 这个函数和下面那个函数是一个东西啊
    def wrapper(self, *args, **kwargs):
        return method(self, *args, **kwargs)

    return wrapper


def coordinate_gui(method):  # 同时GUI 模拟的状态
    """
    Wrapper funciton, informs the gui about the
    status of the simulation
    """

    @functools.wraps(method)  # 这个装饰器在方法执行前后与协调器进行交互。
    def wrapper(self, *args, **kwargs):
        if self.coordinator is not None:  # 如果设备有协调器
            self.coordinator.start_processing()  # 调用协调器函数start_processing()
        x = method(self, *args, **kwargs)  # 执行被装饰的方法，并将结果存储在 x 中。
        if self.coordinator is not None:  # 方法执行后，调用 self.coordinator.processing_finished()
            self.coordinator.processing_finished()
        return x  # 返回方法的结果x

    return wrapper


def schedule_next_event(method):  # schedule_next_event 是一个装饰器，用于在被装饰方法执行后，调度下一个设备事件。
    """
    Schedules the next device event, if it exists
    """
     # 这个装饰器用于处理方法返回的结果，并为连接的设备和端口调度新事件。
    @functools.wraps(method)
    def wrapper(self, time, *args, **kwargs):
        results = method(self, time, *args, **kwargs)  # 调用被装饰的方法 method，传递 self、time 以及其他参数 *args 和 **kwargs，并获取其返回结果 results
        if results is None:  # 检查结果是否为空
            return           # 如果结果为空就直接返回，没有其他操作
        for output_port, signal, time in results:  # 遍历结果中的每个三元组
            next_device, port = self.get_next_device_and_port(output_port)  # 调用 self.get_next_device_and_port(output_port) 获取与输出端口连接的下一个设备和端口。
            if not next_device is None:  # 检查下一个设备是否存在：如果下一个设备不是空的
                time_as_float = float(time)   # 将时间转换为浮点数
                l = get_custom_logger(Loggers.Devices)  # 获取自定义日志记录器，用于记录和设备相关的信息
                if self.name is None:  # 如果当前设备没有名字
                    if next_device.name is None:  # 下一个设备也没有名字
                        formatted_message = (  # 格式化日志信息 formatted_message，包括时间、设备名称和类名。
                            "<{:.3e}s> {} is scheduling new event for {}".format(
                                time_as_float,
                                self.__class__.__name__,   # 当前设备没有名字，用类名进行标识
                                next_device.__class__.__name__,  # 下一个设备没有名字，用类名进行标识
                                time_as_float,
                            )
                        )
                    else:  # 如果下一个设备有名字，就正常使用下一个设备的名字
                        formatted_message = (
                            "<{:.3e}s> {} is scheduling new event for {} ({})".format(
                                time_as_float,
                                self.__class__.__name__,
                                next_device.name,
                                next_device.__class__.__name__,
                                time_as_float,
                            )
                        )
                else:  # 如果当前设备有名字
                    formatted_message = (
                        "<{:.3e}s> {} ({}) is scheduling new event for {} ({})".format(
                            time_as_float,
                            self.name,  # 就正常使用当前设备的名字
                            self.__class__.__name__,
                            next_device.name,
                            next_device.__class__.__name__,
                            time_as_float,
                        )
                    )
                l.info(formatted_message)  # 将格式化后的日志信息 formatted_message 记录到日志中
                signals = {port: signal}   # 创建一个信号字典，键位port，键值为signal
                self.simulation.schedule_event(time, next_device, signals=signals)  # 调用 self.simulation.schedule_event 方法，
                                                                                    # 为下一个设备 next_device 在指定时间 time 调度事件，并传递信号 signals。

    return wrapper


class GenericDevice(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """  # GenericDevice继承了一个抽象基类

    def __init__(self, name=None, uid=None):  # 对实例进行初始化，给对象赋予初始状态和属性
        """
        Initialization method
        """
        self.name = name   # 表示设备名称
        self.ports = deepcopy(self.__class__.ports)  # 深拷贝self.__class__.ports，使每个设备都有自己独立的端口副本
        if hasattr(self.__class__, "values"):  # hasattr：用来判断对象是否具有对应的属性或者方法。如果class中属性values存在，
            self.values = deepcopy(self.__class__.values)  # 将其深拷贝到self.values
        for port in self.ports.keys():  # port是字典。对于那些在self port中的port
            self.ports[port].device = self  # 设置这些端口的device属性，指向当前设备实例

        simulation = Simulation.get_instance()  # 获取simulation的单例实例
        ref = DeviceInformation(name=name, obj_ref=self, uid=uid)  # 创建DeviceInformation的对象 ref，包含设备名称、引用和唯一标识符
        self.ref = ref
        simulation.register_device(ref)  # 将device注册到模拟环境中
        self.coordinator = None  # 初始化coordinator和simulation属性
        self.simulation = Simulation.get_instance()

    def register_signal(  # 注册信号方法：用于将信号注册到指定端口
        self, signal: GenericSignal, port_label: str, override: bool = False
    ):
        """
        Register a signal to port
        """
        port = None
        try:
            port = self.ports[port_label]  # 尝试获取指定标签的端口
        except KeyError as exc:            # 如果端口不存在，抛出异常
            raise NoPortException(
                f"Port with label {port_label} does not exist."
            ) from exc

        if port.signal is not None:  # 如果端口有信号连接
            if not override:   # 该信号连接 没有覆盖已存在的信号
                raise PortConnectedException(  # 抛出异常，提示信号已经注册
                    f"Signal was already registered for the port\n"
                    + "If this is intended, set override to True\n"
                    + f"Device: {type(self)}, {self.name}, {self.ref.uuid}\n"
                    + f"Port: {type(port.signal)}, {port_label}"
                )

        if not (  # 如果端口没有信号连接
            isinstance(signal, port.signal_type)  # 检查当前信号和端口支持的信号类型是否匹配
            or issubclass(type(signal), port.signal_type)
        ):
            raise PortSignalMismatchException(    # 如果不匹配，抛出异常
                "This port does not support selected signal"
            )

        signal.register_port(port, self)  # 调用注册端口的方法，将信号注册到端口
        port.signal = signal   # 将端口的 signal 属性设置为当前信号

    @property
    @abstractmethod
    def ports(self) -> Dict[str, Type["Port"]]:
        """Average Power Draw"""
        raise NotImplementedError("power must be defined")

    @property
    @abstractmethod
    def gui_name(self):
        """Gui name"""
        raise NotImplementedError("gui_name must be defined")

    @property
    @abstractmethod
    def gui_icon(self):
        """Gui name"""
        raise NotImplementedError("gui_icon must be defined")

    @property
    @abstractmethod
    def reference(self):
        """
        Reference is used to compile references for specific
        experiment.
        """
        raise NotImplementedError(
            "reference can be set to None, but must be implemented"
        )

    def set_coordinator(self, coordinator):  # 设置协调器，参数coordinator是协调器对象
        """
        Sets the coordinator
        this is required to have feedback in the gui
        """
        self.coordinator = coordinator  # 将传入的coordinator赋值给self coordinator

    @log_action   # des方法使用@log_action装饰器：就是在不修改被装饰对象源代码和调用方式的前提下为被装饰对象添加额外的功能。
    def des(self, time, *args, **kwargs):  # *args 和 **kwargs 用于传递可变数量的位置参数和关键字参数。
        if hasattr(self, "envelope_backend"):  # 判断self中是否有envelope_backend属性
            self.envelope_backend(*args, **kwargs)  # 如果有，就调用envelope_backend(*args, **kwargs)
        elif hasattr(self, "des_action"):   # 如果没有envelope，则判断是否有des action属性
            self.des_action(time, *args, **kwargs)  # 如果有des action，就调用 self.des_action(time, *args, **kwargs)
        else:  # 如果两个属性都没有，抛出异常，表明必须定义des或des action方法中的一个
            raise DESActionNotDefined("Either des or des_action method must be defined")
        # des 方法用于在指定时间执行离散事件仿真动作，根据是否存在 envelope_backend 或 des_action 属性进行不同的处理。

    def get_next_device_and_port(self, port: str):  # 获取下一个设备和端口。port是端口的标签，是字符串。
        port = self.ports[port]  # 通过port标签获取self ports中对应的端口对象
        if port.signal:   # 如果端口有信号连接
            for connected_port in port.signal.ports:  # 遍历信号连接的所有端口
                if connected_port != port:  # （如果连接的端口不是当前端口）找到与当前端口不同的端口
                    return connected_port.device, connected_port.label  # 返回该端口的设备和标签
        return None, None  # 如果端口没有信号连接（没有找到连接的端口），返回non，none


class DESActionNotDefined(Exception):
    """
    Raised when device should be called with des simulation,
    but des methods are not defined
    """


class NoPortException(Exception):
    """
    Raised when port, which should be accessed doesn't exist
    """


class PortConnectedException(Exception):
    """
    Raised when Signal is already registered for the port.
    """


class PortSignalMismatchException(Exception):
    """
    Raised when signal doesn't match the port description
    """
