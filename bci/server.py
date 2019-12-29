import sys
import signal
import threading

from pathlib import Path

from . import Thought
from .utils import Listener, Hello, Config, Snapshot
from .utils import TranslationParser, ColorImageParser

CONFIG_FIELDS = ['translation', 'color_image']


def run_server(address, data_dir):
    listener = Listener(port=address[1], host=address[0])
    with listener:
        while True:
            connection = listener.accept()
            handler = Handler(connection, data_dir)
            handler.start()


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

    def __init__(self, connection, datapath):
        super().__init__()
        self.connection = connection
        self.datapath = datapath

    def run(self):

        # receive hello message from client
        hello_msg = self.connection.receive_message()
        hello_msg = Hello.deserialize(hello_msg)

        # send config message to client
        config_msg = Config(CONFIG_FIELDS)
        self.connection.send_message(config_msg.serialize())

        # receive snapshot message from client
        snapshot_msg = self.connection.receive_message()
        snapshot = Snapshot.deserialize(snapshot_msg)

        # parse the received snapshot
        self.lock.acquire()     # <- critical section here
        try:
            # parse translation
            parser = TranslationParser(self.datapath, hello_msg)
            parser.parse(snapshot)
            # parse color image
            parser = ColorImageParser(self.datapath, hello_msg)
            parser.parse(snapshot)
        finally:
            self.lock.release()


def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
