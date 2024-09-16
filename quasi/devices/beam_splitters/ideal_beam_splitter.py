"""
Ideal Beam Splitter
"""

import heapq
import mpmath

from quasi.devices.generic_device import (
    GenericDevice,
    log_action,
    ensure_output_compute,
    schedule_next_event,
    wait_input_compute,
)
from quasi.devices.port import Port
from quasi.simulation import Simulation
from quasi.extra import Reference
from quasi.signals import GenericQuantumSignal
from quasi.gui.icons import icon_list

from photon_weave.state.envelope import Envelope
from photon_weave.state.composite_envelope import CompositeEnvelope
from photon_weave.operation.composite_operation import (
    CompositeOperation,
    CompositeOperationType,
)

# 引用一个文献
_BEAM_SPLITTER_BIB = {
    "title": "Quantum theory of the lossless beam splitter",
    "author": "Fearn, H and Loudon, R",
    "journal": "Optics communications",
    "volume": 64,
    "number": 6,
    "pages": "485--490",
    "year": 1987,
    "publisher": "Elsevier",
}

_BEAM_SPLITTER_DOI = "10.1016/0030-4018(87)90275-6"


class PhotonEvent:  # 光子事件表示光子信号在特定时间到达分束器的某个输入端口。分束器会处理这些光子事件，并将输入信号分成两个输出信号。
    def __init__(self, mean_time, std_dev, port, *args, **kwargs):
        self.port = port    # 事件发生的端口
        self.mean_time = mean_time  # 事件的平均时间
        self.std_dev = std_dev  # 事件的标准差
        self.args = args
        self.kwargs = kwargs


class IdealBeamSplitter(GenericDevice):  # 定义一个理想分束器，继承了GenericDevice类
    """
    Ideal Beam Splitter Device
    """
# 分束器有四个端口，AB为输入端口，CD为输出端口
    ports = {  # 定义端口的名字，方向，与该端口匹配的信号类型，端口所属的设备
        "A": Port(
            label="A",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "B": Port(
            label="B",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "C": Port(
            label="C",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "D": Port(
            label="D",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    power_average = 0  # 平均功率和最大功率，一些其他属性
    power_peak = 0
    reference = Reference(doi=_BEAM_SPLITTER_DOI, bib_dict=_BEAM_SPLITTER_BIB) #引用的信息
    processing_time = mpmath.mpf("1e-9")  # 事件处理时间

    gui_icon = icon_list.BEAM_SPLITTER  # 一些GUI的属性
    gui_tags = ["ideal"]
    gui_name = "Ideal Beam Splitter"
    gui_documentation = "ideal_beam_splitter.md"

    def __init__(self, name=None, uid=None):  # 分束器的构造函数，包括设备名称和唯一标识符
        super().__init__(name=name, uid=uid)  # 用super调用父类 GenericDevice 的构造函数，传递 name 和 uid
        self.incomming_photons = []  # 列表，用于存储接受到的光子事件
        self.scheduled_event_time = None  # 用于记录计划的事件time

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """  # 等待计算输入信号，然后使用此方法计算输出
        pass

    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        # Check if this call is for processing or for scheduling
        if kwargs.get("process_now", False):  # 检查kwarg中是否含有process now键，其键值为false
            self.process_delayed_events(time)   # 如果有，则调用process_delayed_events函数处理time（如果不能现在处理，则延迟处理）
        signals = kwargs.get("signals", {})  # 获取字典signals，默认为空字典
        new_events = []  # 初始化 new_events 列表以存储新的光子事件。
        if "A" in signals:  # 检查字典中是否含有A的信号（如果A中有信号）：（检查是否从A端口进入）
            envelope_A = signals["A"].contents  # 获取端口A的内容
            std_dev_A = envelope_A.temporal_profile.get_std_dev()  # 获取端口A的时间分布标准差
            new_events.append(PhotonEvent(time, std_dev_A, "A", signals=signals))  # 创建一个新的A的光子事件并添加到new event列表中
        if "B" in signals:  # 对于端口B有同样的处理
            envelope_B = signals["B"].contents
            std_dev_B = envelope_B.temporal_profile.get_std_dev()
            new_events.append(PhotonEvent(time, std_dev_B, "B", signals=signals))

        self.incomming_photons.extend(new_events)  # 将新创建的光子事件添加到列表incomming photons中
        if new_events:  # 对于这个新的光子事件
            delay_time = max(   # 计算最大延迟时间：标准差的平方×一个常数
                mpmath.mpf(10) * mpmath.mpf(event.std_dev) ** 2 for event in new_events
            )
            print(f"Delay Time: {delay_time}")  # 把延迟时间打印出来
            new_scheduled_time = mpmath.mpf(time) + delay_time  # 计算new_scheduled_time=当先时间+延迟时间
            if (
                self.scheduled_event_time is None  # 如果原本没有调度时间
                or new_scheduled_time > self.scheduled_event_time  # 或者新的调度时间大于原本的调度时间
            ):
                self.scheduled_event_time = new_scheduled_time  # 用新调度时间更新原本的调度时间
                simulation = Simulation.get_instance()  # 获取仿真实例 simulation
                simulation.schedule_event(  # 调度事件，在 self.scheduled_event_time 时间点调用自身，并设置 process_now=True
                    self.scheduled_event_time, self, process_now=True
                )

    @schedule_next_event  # 光子事件在到达时会被延迟处理，确保所有输入信号都被正确处理后，再生成输出信号。
    def process_delayed_events(self, time):  # 定义用于处理延迟光子事件的方法
        results = []  # 初始化一个result列表用于存储生成的结果
        if len(self.incomming_photons) == 1:   # 如果光子事件的长度只有1（只有一个光子事件）
            pe = self.incomming_photons[0]     # 设置incoming_photons列表的索引0
            env1 = pe.kwargs["signals"][pe.port].contents  # 获取pe的信号内容
            env2 = Envelope()  # 设置实例2为envelope
            ce = CompositeEnvelope(env1, env2)  # 把两个事件合并到一起，生成新的时间ce，联合时间
            op = CompositeOperation(CompositeOperationType.NonPolarizingBeamSplit)  # 创建CompositeOperation实例op，指定为非偏振分束器操作
            if pe.port == "A":  # 如果光子事件pe的端口是A
                ce.apply_operation(op, env1, env2)  # 将op操作应用到ce（事件1和事件2）中
                sig1 = GenericQuantumSignal()  # 创建一个GenericQuantumSignal的实例，叫sig1
                sig1.set_contents(env1)   # 设置sig1的内容为env1
                sig2 = GenericQuantumSignal()
                sig2.set_contents(env2)
            else:  # 如果光子事件pe的端口是B，有类似的操作
                ce.apply_operation(op, env2, env1)
                sig1 = GenericQuantumSignal()
                sig1.set_contents(env2)  # 设置sig1的内容为env2
                sig2 = GenericQuantumSignal()
                sig2.set_contents(env1)  # 设置sig2的内容为env1

            results.append(  # 将结果添加到result列表，输出端口为C和D，时间为……
                ("C", sig1, pe.mean_time + IdealBeamSplitter.processing_time)
            )
            results.append(
                ("D", sig2, pe.mean_time + IdealBeamSplitter.processing_time)
            )  # 对单个光子事件，应用非偏振分束器操作，生成两个输出信号。
#  对多个光子事件，计算时间差和信号重叠，应用非偏振分束器操作，生成多个输出信号。
        elif len(self.incomming_photons) > 1:  # 如果有多个光子事件：表示在同一时刻或接近时刻有多个光子信号到达分束器的不同输入端口。
            for i in range(len(self.incomming_photons)):  # 遍历所有光子事件，索引为i
                for j in range(i + 1, len(self.incomming_photons)):  # 内层循环从 i + 1 开始遍历剩余的光子事件，索引为 j
                    p1 = self.incomming_photons[i]  # 获取索引 i 处的光子事件 p1 （不同的A和B端口产生了嵌套光子时间）
                    p2 = self.incomming_photons[j]  # 获取索引 j 处的光子事件 p2

                    if p1.port != p2.port:  # 判断两个光子事件的端口是否不同，如果不同
                        time_dif = abs(p1.mean_time - p2.mean_time)  # 计算两个端口的时间差并打印
                        print(f"Time_dif:{time_dif}")
                        env1 = p1.kwargs["signals"][p1.port].contents  # 获取 p1 对应端口的信号内容 env1
                        env2 = p2.kwargs["signals"][p2.port].contents  # 获取 p2 对应端口的信号内容 env2
                        overlap = float(env1.overlap_integral(env2, time_dif))
                        print(f"Overlap: {overlap}")  # 计算env1和env2在time_dif时间差下的重叠积分overlap并打印
                        # overlap = 1
                        ce = CompositeEnvelope(env1, env2)  # 创建包含 env1 和 env2 的复合信号 ce
                        op = CompositeOperation(  # 创建非偏振分束器操作 op，并设置重叠值 overlap
                            CompositeOperationType.NonPolarizingBeamSplit,  # 非偏振分束器操作是量子操作的一种类型，用于模拟分束器对光子信号的处理。
                            overlap=overlap,  # 在这个操作中，输入信号被分成两个输出信号，这两个输出信号具有一定的重叠和关联。
                        )
                        if p1.port == "A":
                            ce.apply_operation(op, env1, env2)
                            sig1 = GenericQuantumSignal()
                            sig1.set_contents(env1)
                            sig2 = GenericQuantumSignal()
                            sig2.set_contents(env2)
                        else:
                            ce.apply_operation(op, env2, env1)
                            sig1 = GenericQuantumSignal()
                            sig1.set_contents(env2)
                            sig2 = GenericQuantumSignal()
                            sig2.set_contents(env1)
                        results.append(  # 将结果追加到 results 列表中
                            (  # 结果包含输出端口 "C"、信号 sig1、时间…………
                                "C",
                                sig1,
                                p1.mean_time + IdealBeamSplitter.processing_time,
                            )
                        )
                        results.append(
                            (
                                "D",
                                sig2,
                                p2.mean_time + IdealBeamSplitter.processing_time,
                            )
                        )
        self.incomming_photons = []  # 清空 self.incoming_photons 列表
        return results   # 返回 results 列表，其中包含了生成的光子事件及其信息。