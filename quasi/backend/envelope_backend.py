from photon_weave.state.envelope import Envelope

class EnvelopeBackend():

    def __init__(self): # 类的方法。初始化了EnvelopeBackend对象
        self.number_of_modes = 0 # 设置number_of_modes为0

    def set_number_of_modes(self, number_of_modes): # 方法。用于设置当前系统中量子模式的数量
        self.number_of_modes = number_of_modes

    def new_envelope(self): # 方法。创建一个新的envelope对象并返回
        return Envelope()
    # Envelope 类可能是一个封装量子态操作或参数的类。通过调用 new_envelope 方法，
    # 后端可以生成一个新的空信封，用于后续的操作（如在量子模式上施加操作或记录状态）
