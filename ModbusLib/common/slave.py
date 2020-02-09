import re
import time
import uuid
import datetime

from ModbusLib.common.utils import logger as logging
from ModbusLib.common import exceptions, config_handler
from multiprocessing import Queue
from twisted.internet import reactor
from twisted.internet import error as twisted_error
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
import threading
ROOT_DIR = config_handler.ROOT_DIR

logger = logging.setup('Slave')


class Slave:

    def __init__(self, config, _id, queue):
        handle = config
        # print(handle)
        self._id = _id
        self.port = int(handle['port'])
        self.di = handle['di']
        self.co = handle['co']
        self.hr = handle['hr']
        self.ir = handle['ir']
        self.t = None
        logger.info(handle)
        self.data_queue: Queue = queue
        self.store = ModbusSlaveContext(
            di=CallbackDataBlock(self.data_queue, 0, self._id),
            co=CallbackDataBlock(self.data_queue, 1, self._id),
            hr=CallbackDataBlock(self.data_queue, 2, self._id),
            ir=CallbackDataBlock(self.data_queue, 3, self._id))
        self.handle = handle
        self.identity = ModbusDeviceIdentification()
        self.context = ModbusServerContext(slaves={0: self.store}, single=False)

    def get_data(self):
        di = self.store.store['d'].getAllValues()
        co = self.store.store['c'].getAllValues()
        hr = self.store.store['h'].getAllValues()
        ir = self.store.store['i'].getAllValues()
        self.data_queue.put([self._id, 0, self.di['start'], di])
        self.data_queue.put([self._id, 1, self.co['start'], co])
        self.data_queue.put([self._id, 2, self.hr['start'], hr])
        self.data_queue.put([self._id, 3, self.ir['start'], ir])

    def process(self):
        logger.info(f"Starting modbus server on port {self.port}")
        try:
            self.t = threading.Thread(target=StartTcpServer, args=(self.context, self.identity, ('localhost', self.port)))
            self.t.start()
            logger.info(self.context)
        except twisted_error.CannotListenError as e:
            logger.info(e)


class CallbackDataBlock(ModbusSequentialDataBlock):

    def __init__(self, queue, rtype, _id):
        self.queue = queue
        self.rtype = rtype
        self._id = _id
        super().__init__(0x00, [0x00]*66536)

    def getAllValues(self):
        return self.values

    def setValues(self, address, values):
        self.queue.put([self._id, self.rtype, address, values])
        super().setValues(address, values)
