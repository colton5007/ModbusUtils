import json
import time

from datetime import timedelta

from ModbusLib.common import config_handler, slave_handler, client_handler
from ModbusLib.common.utils import logger as logging
from multiprocessing import Process, Pipe, Queue

logger = logging.setup(__name__)


# logger.setLevel(logging.DEBUG)


class ProcessHandler(Process):

    def __init__(self, pipe: Pipe, viewer_queue: Queue):
        Process.__init__(self)
        self.slave_conn, self.sc_child = Pipe()
        self.viewer_queue = viewer_queue
        self.slaves = slave_handler.SlaveHandler(self.sc_child, self.viewer_queue)
        self.client = client_handler.Client()
        self.started = False
        self.rx_count = 0
        self.tx_count = 0
        self.rx_rate = 0
        self.tx_rate = 0
        self.start_time = 0
        self.pipe = pipe
        self.run_flag = True
        self.stat_cache = (self.rx_count, self.tx_count, self.start_time)

    def run(self):
        self.start_process()
        prev_time = time.time()
        while self.run_flag:
            self.handle_commands()
            self.update_stats()

            cur_time = time.time()
            scan_time = prev_time - cur_time
            if scan_time > 0.1:
                logger.info(f"Scan time: {scan_time}")
            prev_time = cur_time

    def update_stats(self):
        rxc, txc, lt = self.stat_cache
        cur_time = int(time.time())
        if cur_time % 10 == 0 and cur_time != lt:
            self.rx_rate = (self.rx_count - rxc) / 10
            self.tx_rate = (self.tx_count - txc) / 10
            self.stat_cache = (self.rx_count, self.tx_count, cur_time)

    def handle_commands(self):
        while self.pipe.poll():
            command = self.pipe.recv()
            cmd_name = command['name']
            if cmd_name == 'start':
                self.start_process()
            elif cmd_name == 'stop':
                self.stop_process()
            elif cmd_name == 'update_cfg':
                mode = command['mode']
                new_config = command['new_config']
                status = True
                try:
                    self.update_config(mode, new_config)
                except Exception as ex:
                    logger.warning(ex)
                    status = False
                payload = {
                    'name': 'update_cfg',
                    'status': status
                }
                self.pipe.send(payload)
            elif cmd_name == 'shutdown':
                self.shutdown()
            elif cmd_name == 'fetch_cfg':
                mode = command['mode']
                cfg = self.fetch_config(mode)
                payload = {
                    'name': 'fetch_cfg',
                    'mode': mode,
                    'data': cfg
                }
                self.pipe.send(payload)
            elif cmd_name == 'start_viewer':
                self.pipe.send(command)
            elif cmd_name == 'stop_viewer':
                self.pipe.send(command)
            elif cmd_name == 'fetch_stats':
                payload = {
                    'rxCount': self.rx_count,
                    'txCount': self.tx_count,
                    'uptime': str(timedelta(seconds=(int(time.time() - self.start_time)))),
                    'rxRate': self.rx_rate,
                    'txRate': self.tx_rate
                }
                self.pipe.send(payload)
            elif cmd_name == 'execute':
                fc = int(command['fc'])
                addr = int(command['addr'])
                if fc <= 4:
                    result = self.client.execute(fc, addr, length=(command['length']+1))
                    payload = {
                        'mode': 'client',
                        'f': False,
                        'data': result,
                        'status': True
                    }
                    self.pipe.send(payload)
                else:
                    self.client.execute(fc, addr, values=command['values'])
                    payload = {
                        'mode': 'client',
                        'f': True,
                        'status': True
                    }
                    self.pipe.send(payload)
            elif cmd_name == 'client_setup':
                self.client.setup(command['config'])
                payload = {
                    'mode': 'client',
                    'status': self.client.connect()
                }
                self.pipe.send(payload)
            else:
                pass

    def start_process(self):
        self.start_time = time.time()
        self.slaves = slave_handler.SlaveHandler(self.sc_child, self.viewer_queue)
        self.slaves.setup()
        self.slaves.start()

    def update_config(self, mode, new_config):
        if mode == 'server':
            self.slave_conn.send({
                'name': 'update_cfg',
                'mode': 'server',
                'new_config': new_config
            })
            config_handler.write_new_config(mode, new_config)
        elif mode == 'client':
            self.client.update_config(new_config)
            config_handler.write_new_config(mode, new_config)

    def shutdown(self):
        self.run_flag = False

    def stop_process(self):
        self.shutdown_plugins()

    def fetch_config(self, mode, slave_id=-1):
        if mode == 'client':
            handle = config_handler.load_client_config()
            return handle
        else:
            if slave_id == -1:
                return config_handler.load_slave_config()
            else:
                return config_handler.load_slave_config()[slave_id]

    def init_modbus(self):
        client_handle = config_handler.load_client_config()
        self.client.setup(client_handle)
        self.slaves.setup()

    def shutdown_plugins(self):
        self.slave_conn.send({
            'name': 'shutdown'
        })
