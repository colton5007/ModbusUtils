import requests
from flask import Flask, send_file, send_from_directory, render_template, request
import json
from multiprocessing import Pipe, Queue
import ModbusLib.common.utils.logger as logging
import time
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app, async_mode='threading', manage_session=False)

server_ip = '0.0.0.0'
server_port = 5000

# Client Conf
client_conf = None
client_tcp = None
modbus = None

server_conf = None
slaves = None
selected_slave = 0

viewer = None
viewer_thread = None
viewer_queue = Queue()
viewer_source = {
    'enabled': False,
    'slave_id': 0,
    'name': 'stop_viewer'
}

process_conn, rest_conn = Pipe()

main_process = None
logger = None


def get_client_config():
    global client_conf
    global modbus
    global client_tcp
    start_time = time.time()
    rest_conn.send({'name': 'fetch_cfg', 'mode': 'client'})
    while not rest_conn.poll():
        time.sleep(0.1)
    client_conf = rest_conn.recv()
    # print(dev_conf)
    client_conf = client_conf['data']
    client_tcp = {
        'ip': client_conf['ipv4']['value'],
        'port': client_conf['port']['value']
    }
    modbus = {
        '2_byte_id': client_conf['2_byte_id']['value'],
        'function_code': client_conf['function_code']['value'],
        'register_size': client_conf['register_size']['value'],
        'offset': client_conf['offset']['value'],
        'default': client_conf['default']['value']
    }
    logger.debug(f"Client config fetched in {time.time() - start_time} seconds")


def get_server_config():
    global server_conf
    global slaves
    start_time = time.time()
    rest_conn.send({'name': 'fetch_cfg', 'mode': 'server'})
    while not rest_conn.poll():
        time.sleep(0.1)
    server_conf = rest_conn.recv()
    print(server_conf)
    server_conf = server_conf['data']
    slaves = server_conf
    logger.debug(f"Server config fetched in {time.time() - start_time} seconds")


@app.route('/slaves-live', methods=['GET'])
def slaves_live_serve():
    global viewer, viewer_thread
    cleanup_viewers()
    viewer_source['slave_id'] = selected_slave
    viewer_source['enabled'] = True
    viewer_source['name'] = 'start_viewer'
    rest_conn.send(viewer_source)
    while not rest_conn.poll():
        time.sleep(0.1)
    rest_conn.recv()
    return render_template('slave-live.html')


@app.route('/client-tcp-config', methods=['GET', 'POST'])
def client_tcp_serve():
    global client_tcp
    cleanup_viewers()
    if request.method == 'GET':
        return render_template('client-tcp-config.html', ip=client_tcp['ip'], port=client_tcp['port'], timeout=10)
    else:
        ip = request.form['ip']
        port = request.form['port']
        client_conf['ipv4']['value'] = ip
        client_conf['port']['value'] = port
        # print(f"{ip} {port} {timeout}")
        payload = {
            'name': 'update_cfg',
            'mode': 'client',
            'new_config': client_conf
        }
        client_tcp = {
            'ip': client_conf['ipv4']['value'],
            'port': client_conf['port']['value']
        }
        rest_conn.send(payload)
        while not rest_conn.poll():
            time.sleep(0.1)
        resp = rest_conn.recv()
        payload2 = {
            'name': 'client_setup',
            'mode': 'client',
            'config': client_conf
        }
        rest_conn.send(payload2)
        while not rest_conn.poll():
            time.sleep(0.1)
        resp = rest_conn.recv()
        if resp['status']:
            return 'Client Successfully Connected'
        else:
            return 'Fail'


@app.route('/client-modbus-config', methods=['GET', 'POST'])
def client_modbus_serve():
    global modbus
    cleanup_viewers()
    if request.method == 'GET':
        default_flag = ''
        if modbus['default']:
            default_flag = 'checked'
        id_size = ''
        if modbus['2_byte_id']:
            id_size = 'checked'
        return render_template('client-modbus-config.html', register_size=modbus['register_size'],
                               function_code=modbus['function_code'], default_flag=default_flag, offset=modbus['offset'], id_size=id_size)
    else:
        register_size = request.form['register_size']
        default_flag = 'default_flag' in request.form
        id_size = 'id_size' in request.form
        offset = request.form['offset']
        slave_id = request.form['slave_id']
        starting_address = int(request.form['addr1'])
        end_address = int(request.form['addr2'])
        length = abs(starting_address - end_address)
        function_code = request.form['function_code']
        client_conf['2_byte_id']['value'] = id_size
        client_conf['function_code']['value'] = function_code
        client_conf['register_size']['value'] = register_size
        client_conf['offset']['value'] = offset
        client_conf['default']['value'] = default_flag
        v = request.form['write_values'].split(',')
        if v != [''] and v is not None:
            values = [int(x) for x in v]
        else:
            values = []
        # print(f"{encoding} {remove_whitespace} {separator}")
        payload = {
            'name': 'update_cfg',
            'mode': 'client',
            'new_config': client_conf
        }
        modbus = {
            '2_byte_id': id_size,
            'function_code': function_code,
            'register_size': register_size,
            'offset': offset,
            'default': default_flag
        }
        payload2 = {
            'name': 'execute',
            'fc': function_code,
            'addr': starting_address,
            'length': length,
            'values': values
        }
        rest_conn.send(payload2)
        while not rest_conn.poll():
            time.sleep(0.1)
        resp = rest_conn.recv()
        if resp['status']:
            if not resp['f']:
                return {'data': resp['data']}
            else:
                return 'Success'
        else:
            return 'Fail'

# TODO Modify this to support multiple slaves
@app.route('/server-config', methods=['GET', 'POST'])
def server_config_serve():
    global slaves
    global server_conf
    cleanup_viewers()
    if request.method == 'GET':
        return render_template('server-config.html', slaves=slaves)
    else:
        ip = request.form['ip']
        port = request.form['port']
        slaves = [{
            'ip': ip,
            'port': port
        }]
        server_conf['slaves'] = slaves
        # print(f"{encoding} {remove_whitespace} {separator}")
        payload = {
            'name': 'update_cfg',
            'mode': 'server',
            'new_config': server_conf
        }
        rest_conn.send(payload)
        while not rest_conn.poll():
            time.sleep(0.1)
        resp = rest_conn.recv()
        if resp['status']:
            return 'Server Configuration Applied'
        else:
            return 'Fail'


@app.route('/', methods=['GET'])
def default_page():
    cleanup_viewers()
    get_client_config()
    get_server_config()
    return render_template("index.html", ip=client_tcp['ip'], port=client_tcp['port'], function_code=3, offset=0, slaves=slaves)


@app.route('/assets/<path:path>', methods=['GET'])
def serve_assets(path):
    cleanup_viewers()
    return send_from_directory('assets', path)


@app.route('/start', methods=['GET'])
def start_modbus():
    cleanup_viewers()
    payload = {
        'name': 'start'
    }
    rest_conn.send(payload)
    return 'Starting'


@app.route('/stop', methods=['GET'])
def stop_modbus():
    cleanup_viewers()
    payload = {
        'name': 'stop'
    }
    rest_conn.send(payload)
    return 'Stopping'


@app.route('/stats', methods=['GET'])
def fetch_stats():
    payload = {
        'name': 'fetch_stats'
    }
    rest_conn.send(payload)
    while not rest_conn.poll():
        time.sleep(0.1)
    resp = rest_conn.recv()
    return json.dumps(resp)


@app.route('/shutdown', methods=['GET'])
def shutdown_modbus():
    cleanup_viewers()
    payload = {
        'name': 'shutdown'
    }
    rest_conn.send(payload)
    return 'Terminating process'


@app.route('/upload-slave-config', methods=['POST'])
def upload_slave_config():
    if request.method == 'POST':
        file = request.files['channel-file']

        if file:
            lines: list = file.stream.readlines()
            temp = []
            for line in lines:
                line = str(line, 'ascii').strip()
                temp.append(line.split(','))
            # print(json.dumps(temp))
            return json.dumps(temp)
        return 'Fail'
    else:
        return ''


@app.route('/finalize-slave-config', methods=['POST'])
def finalize_slave_config():
    global slaves
    if request.method == 'POST':
        data = request.form['mapping']
        parsed_slaves = json.loads(data)
        slaves = parsed_slaves
        server_conf['slaves'] = slaves
        payload = {
            'name': 'update_cfg',
            'mode': 'server',
            'new_config': server_conf
        }
        rest_conn.send(payload)
        while not rest_conn.poll():
            time.sleep(0.1)
        resp = rest_conn.recv()
        if resp['status']:
            return 'Slaves configuration applied.'
        else:
            return 'Fail'
    else:
        return 'Fail'


def cleanup_viewers():
    if viewer_source['enabled']:
        payload = viewer_source
        viewer_source['name'] = 'stop_viewer'
        rest_conn.send(payload)
        viewer_source['enabled'] = False


def send_viewer_data(queue: Queue, ):
    while True:
        if not queue.empty():
            # print("Sending reading to viewer")
            data = queue.get()
            if data == 'stop':
                break
            else:
                socketio.emit('viewer', {'ts': data[0], 'payload': data[1]})
        socketio.sleep(1)


@socketio.on('connect')
def start_viewer():
    global viewer_thread
    viewer_thread = socketio.start_background_task(send_viewer_data, viewer_queue)


@socketio.on('test')
def test_socket(data):
    print(data)


if __name__ == '__main__':
    logger = logging.setup(__name__)
    from ModbusLib.process_handler import ProcessHandler

    main_process = ProcessHandler(process_conn, viewer_queue)
    main_process.start()
    socketio.run(app, host=server_ip, port=server_port)
