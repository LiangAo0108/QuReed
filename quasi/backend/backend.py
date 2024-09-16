"""
This module implements the Backend Feature.
"""

from abc import ABC, abstractmethod # 导入abc抽象基
from typing import List
# backend 通常是指后台计算引擎，它负责执行核心计算任务，
# 管理系统资源，以及处理各种操作。它可以与前端（如用户接口或API）进行交互，但通常专注于低级别的计算和处理任务。
class Backend(ABC):
    """
    All Backends are singletons
    """  # backend继承自抽象基类。
    _instances = {} # 类变量，用于存储类的实例。是个字典。字典确保了每个类只能有一个实例。

    def __new__(cls, *args, **kwargs): # 一个特殊方法，用于控制类的实例创建，通常在实例创建之前调用。
        # 如果cls不在字典中，说明还没有创建类的实例
        if cls not in cls._instances: # *args 和 **kwargs 是可变参数，用于将任意数量的非关键字和关键字参数传递给方法。
            cls._instances[cls] = super(Backend, cls).__new__(cls) # 如果不存在就调用父类backend的new方法来创建一个新实例
        return cls._instances[cls] # 然后把新实例存在字典instances中，cls是key


class FockBackend(Backend): # backend继承自抽象基，Fockbackend继承自backend，可以被实例化
    """
    This class enforces the structure of the Fock Backends 这个类强制执行Fock后端结构
    """
# 这里展示出Fockbackend的所有使用过的抽象方法
    @abstractmethod # 用于在abc中定义抽象方法的装饰器，必须实现backend中所有的抽象方法才可以实例化Fockbackend
    def set_number_of_modes(self, number_of_modes):
        """
        Tells the backend number of modes that should be simulated 告诉后端应该模拟的模式数
        """

    @abstractmethod
    def create(self, mode):
        """
        Should return creation operator 应该返回创建操作符
        """

    @abstractmethod
    def destroy(self, mode):
        """
        Should return annihilation method
        """

    @abstractmethod
    def squeeze(self, z: complex, mode):
        """
        Should return squeezing operator
        """

    @abstractmethod
    def displace(self, alpha: float, phi: float, mode):
        """
        Should return displacement operator
        """

    @abstractmethod
    def phase_shift(self, theta: float, mode):
        """
        Should return phase shift operator
        """

    @abstractmethod
    def number(self, mode):
        """
        Should return number operator
        """

    @abstractmethod
    def apply_operator(self, operator, modes: List[int]):
        """
        Should Apply the operator to the correct mode
        """
