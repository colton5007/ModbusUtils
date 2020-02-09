from ModbusLib.common.utils import logger as logging
import json
import os.path

ROOT_DIR = os.getcwd() + '\\ModbusLib\\'
logger = logging.setup(__name__)


def load_slave_config():
    logger.info('Attemping to read client config')
    slave_handles = []
    file = f"{ROOT_DIR}config\\server\\server"
    if os.path.isfile(file):
        slave_handles = json.loads(open(file, 'r').read())['slaves']['value']['data']
    return slave_handles


def load_client_config():
    logger.info('Attemping to read server config')
    client_handle = {}
    file = f"{ROOT_DIR}config\\client\\client"
    if os.path.isfile(file):
        client_handle = json.loads(open(file, 'r').read())
    return client_handle


def write_new_config(mode, new_config):
    logger.info(f"Writing new config for {mode} mode")
    with open(f'{ROOT_DIR}config\\{mode}\\{mode}', 'w') as cfile:
        cfile.write(json.dumps(new_config))


def apply_default_config(default_config):
    handle = {}
    for key in default_config:
        handle[key] = default_config[key]
        handle[key]['value'] = handle[key]['default']
    return handle


def load_single_config(mode):
    file = f"{ROOT_DIR}config/{mode}/{mode}"
    if os.path.isfile(file):
        handle = json.loads(open(file, 'r').read())
        return handle
    return None