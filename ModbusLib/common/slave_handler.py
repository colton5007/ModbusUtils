from multiprocessing import Process, Queue
from ModbusLib.common.utils import logger as logging
from ModbusLib.common import config_handler
from ModbusLib.common.slave import Slave
from twisted.internet import reactor
logger = logging.setup(__name__)


class SlaveHandler(Process):

    def __init__(self, conn, viewer_queue):
        Process.__init__(self)
        self.active_viewers = []
        self.viewer_queue = viewer_queue
        self.data_queue = Queue()
        self.slave_handles = []
        self.slaves = []
        self.conn = conn
        self.run_flag = True

    def run(self):
        slave = self.slaves[0]
        slave.process()
        while self.run_flag:
            self.handle_commands()
            self.update_viewers()

    def setup(self):
        self.slave_handles = config_handler.load_slave_config()
        for i in range(len(self.slave_handles)):
            self.slaves.append(Slave(self.slave_handles[i], i, self.data_queue))
        logger.info("Initialized Slaves")

    def update_viewers(self):
        if not self.data_queue.empty():
            update = self.data_queue.get()
            _id = update[0]
            if _id in self.active_viewers:
                self.viewer_queue.put(update)

    def fetch_data(self, _id):
        self.slaves[_id].get_data()

    def handle_commands(self):
        if self.conn.poll():
            command = self.conn.recv()
            cmd_name = command['name']
            logger.debug(command)
            if cmd_name == 'start_viewer':
                slave_id = command['slave_id']
                if slave_id not in self.active_viewers:
                    self.active_viewers.append(slave_id)
                self.fetch_data(slave_id)
            elif cmd_name == 'stop_viewer':
                slave_id = command['slave_id']
                if slave_id in self.active_viewers:
                    self.active_viewers.remove(slave_id)
            elif cmd_name == 'update_cfg':
                new_config = command['new_config']
                logger.info(f"Updating slave config")
                for i in range(len(new_config)):
                    self.slave_handles[i] = new_config[i]
                    self.slaves[i].reconfigure(new_config[i])
            elif cmd_name == 'shutdown':
                self.shutdown()

    def shutdown(self):
        self.run_flag = False
