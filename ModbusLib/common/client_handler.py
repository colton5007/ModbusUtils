from pymodbus.client.sync import ModbusTcpClient


class Client:

    def __init__(self):
        self.client = None
        self.handle = None
        self.ip = '127.0.0.1'
        self.port = 502

    def setup(self, config):
        self.handle = config
        self.ip = config['ipv4']['value']
        self.port = config['port']['value']
        self.client = ModbusTcpClient(self.ip, self.port)

    def execute(self, fc, addr, length=1, values=None):
        result = None
        if fc == 1:
            temp = self.client.read_coils(addr, length)
            result = []
            for i in range(temp.byte_count):
                t2 = temp.bits[i*16:(i+1)*16]
                result.append(''.join([str(int(x)) for x in t2]))
        elif fc == 2:
            temp = self.client.read_discrete_inputs(addr, length)
            result = []
            for i in range(temp.byte_count):
                t2 = temp.bits[i*16:(i+1)*16]
                result.append(''.join([str(int(x)) for x in t2]))
        elif fc == 3:
            temp = self.client.read_holding_registers(addr, length).registers
            result = ['{0:016b}'.format(x) for x in temp]
        elif fc == 4:
            temp = self.client.read_input_registers(addr, length).registers
            result = ['{0:016b}'.format(x) for x in temp]
        elif fc == 5:
            if values:
                self.client.write_coil(addr, values[0])
        elif fc == 6:
            if values:
                self.client.write_register(addr, values[0])
        elif fc == 15:
            if values:
                self.client.write_coils(addr, values)
        elif fc == 16:
            if values:
                self.client.write_registers(addr, values)
        return result

    def update_config(self, conf):
        self.ip = conf['ipv4']['value']
        self.port = conf['port']['value']
        self.client = ModbusTcpClient(self.ip, self.port)
        self.handle = conf

    def connect(self):
        return self.client.connect()
