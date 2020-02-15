import sys
import signal
import struct
import threading
from pathlib import Path

import click
from furl import furl

from . import Thought
from .utils import Listener, UserData, Snapshot, VERSION, DATA_DIR, MSG_TYPES

#EX-6
def run(port, datapath):
    listener = Listener(port=int(port), host='127.0.0.1')
    with listener:
        while True:
            connection = listener.accept()
            handler = Handler(connection, datapath)
            handler.start()


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
            self.publish.publish(message, msg_type, user_id, **self.kwargs)
        except Exception as e:
            self.connection.send_message(f'ERROR: {e.args[0]}')
            return
        self.connection.send_message('OK!')


def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Final project
@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass

@cli.command()
@click.option('-h', '--host')
@click.option('-p', '--port', type=int)
@click.argument('message-queue-url')
def run_server(host, port, message_queue_url):
    # retrieve publisher module
    message_queue_url = furl(message_queue_url)
    publisher = __import__(f'bci.publishers.{message_queue_url.scheme}',
                           globals(),
                           locals(),
                           [message_queue_url.scheme])
    try:
        _run_server(host, port, publish=publisher,
                    publisher_host=message_queue_url.host,
                    publisher_port=message_queue_url.port)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1

def _run_server(host, port, publish, **kwargs):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8000

    listener = Listener(port=port, host=host)
    with listener:
        while True:
            connection = listener.accept()
            handler = Handler(connection, DATA_DIR, publish, **kwargs)
            handler.start()


# API function aliases
run_server = _run_server

if __name__ == '__main__':
    cli(prog_name='bci.server')
