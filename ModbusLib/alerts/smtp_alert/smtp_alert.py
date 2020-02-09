import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ModbusLib.common.utils import logger as logging

logger = logging.setup(__name__)

_MODULE_NAME = 'smtp_alert'
_MODULE_DESC = 'Plugin for sending SMTP Alerts'
_DEFAULT_CONFIG = {
    'host': {
        'description': 'The SMTP Server hostname.',
        'type': 'string',
        'default': 'smtp.office365.com',
        'displayName': 'Server Hostname'
    },
    'sender': {
        'description': 'The SMTP Sender.',
        'type': 'string',
        'default': 'colton@levelops.com',
        'displayName': 'Sender Email'
    },
    'password': {
        'description': 'The SMTP Sender Password.',
        'type': 'string',
        'default': '1R@900m!',
        'displayName': 'Sender Password'
    },
    'port': {
        'description': 'The SMTP Server port.',
        'type': 'integer',
        'default': '587',
        'displayName': 'Server Port'
    }
}

ser = None
logging.setup(_MODULE_NAME)


def plugin_info():
    _plugin_info = {
        'name': _MODULE_NAME,
        'version': "1.0.0",
        'config': _DEFAULT_CONFIG
    }

    return _plugin_info


def send_alert(handle, destination, msg):
    try:
        server = smtplib.SMTP(host=handle['host']['value'], port=int(handle['port']['value']), timeout=10)
        server.starttls()
        server.login(handle['sender']['value'], handle['password']['value'])
        message = MIMEMultipart('alternative')
        message["Subject"] = "Site Singularity Alert"
        message["From"] = handle['sender']['value']
        message["To"] = destination

        html = """\
                   <html>
                     <body>
                        %s
                     </body>
                   </html>
                   """ % (msg)
        part = MIMEText(html, "html")
        message.attach(part)
        text = message.as_string()
        server.sendmail(handle['sender']['value'], destination, text)
        server.quit()
        logger.info(f"Sent SMTP Alert with message {msg}")
        return True
    except Exception as ex:
        return False
