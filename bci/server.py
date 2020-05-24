import os
import sys
import signal
import struct
import logging
import threading
from pathlib import Path

import click
from furl import furl

from .utils import Listener, UserData, Snapshot, VERSION, DATA_DIR, MSG_TYPES

def logger_init(name):
    log_dir = Path(__file__).parents[1] / "log"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                        filename=log_dir / f"{name}.log",
                        level=logging.DEBUG)
    logging.getLogger(name).setLevel(logging.DEBUG)
    logging.getLogger("pika").propagate = False

class Handler(threading.Thread):
    lock = threading.Lock()

    def __init__(self, connection, datapath, publish, **kwargs):
        super().__init__()
        self.connection, self.datapath, self.publish, self.kwargs = \
            connection, datapath, publish, kwargs

    def run(self):
        # receive message from client
        try:
            message = self.connection.receive_message()
        except Exception as e:
            self.connection.send_message(f'ERROR: {e.args[0]}')
            return

        # deserialize message using protobuf3
        try:
            msg_type, user_id = struct.unpack('<IQ', message[:12])
            if msg_type == MSG_TYPES.USER_DATA:
                message = UserData.deserialize(message[12:])
            elif msg_type == MSG_TYPES.SNAPSHOT:
                message = Snapshot.deserialize(message[12:])
            else:
                self.connection.send_message(f'ERROR: Unknown message type')
        except Exception as e:
            self.connection.send_message(f'ERROR deserializing message')
            return

        # publish message using the provided publish service
        try:
            self.kwargs['msg_type'] = msg_type
            self.kwargs['user_id'] = user_id
            self.publish(message, **self.kwargs)
        except ConnectionError as e:
            print(f'ERROR: {e.args[0]}', file=sys.stderr)
            logging.critical(e.args[0])
            self.connection.send_message(f'ERROR: {e.args[0]}')
            os._exit(1)

        except Exception as e:
            self.connection.send_message(f'ERROR: {e.args[0]}')
            return
        self.connection.send_message('OK!')


def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@click.option('-h', '--host')
@click.option('-p', '--port', type=int)
@click.argument('message-queue-url')
def run_server(host, port, message_queue_url):
    logger_init('server')
    # retrieve publisher module
    message_queue_url = furl(message_queue_url)
    try:
        publisher = __import__(f'bci.publishers.{message_queue_url.scheme}',
                               globals(),
                               locals(),
                               [message_queue_url.scheme])
    except ModuleNotFoundError:
        error = f'Publisher module "{message_queue_url.scheme}" does not exist'
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1
    try:
        _run_server(host, port, publish=publisher.publish,
                    publisher_host=message_queue_url.host,
                    publisher_port=message_queue_url.port)
    except Exception as error:
        if 'Temporary failure in name resolution' in str(error):
            error = f'unknown host name "{host}"'
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1


def _run_server(host=None, port=None, publish=None, **kwargs):
    logger_init('server')
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8000
    if not publish:
        error = 'no publisher function provided'
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1

    listener = Listener(port=port, host=host)
    with listener:
        print('Press CTRL+C to exit')
        while True:
            connection = listener.accept()
            handler = Handler(connection, DATA_DIR, publish, **kwargs)
            handler.start()


# API function aliases
run_server = _run_server

if __name__ == '__main__':
    cli(prog_name='bci.server')
