import socket, struct, time, sys, signal
from .cli import CommandLineInterface
from .thought import Thought
from datetime import datetime
from pathlib import Path
import threading
from .utils.listener import Listener


def run_server(address, data_dir):
    listener = Listener(port=address[1], host=address[0])
    listener.start()
    while True:
        connection = listener.accept()
        handler = Handler(connection, data_dir)
        handler.start()


class Handler(threading.Thread):
    lock = threading.Lock()
    def __init__(self, connection, data_dir):
        super().__init__()
        self.connection = connection
        self.data_dir = data_dir
    def run(self):
        data = bytes()
        while True:
            new_data = self.connection.socket.recv(1024)
            if not new_data:
                break
            data += new_data
        thought = Thought.deserialize(data)
        filename = thought.timestamp.strftime('%Y-%m-%d_%H-%M-%S.txt')
        # handle logging to file
        dir_path = Path(self.data_dir, str(thought.user_id))
        dir_path.mkdir(parents=True, exist_ok=True)
        log_path = Path(dir_path, filename)
        self.lock.acquire()     # <- critical section here
        try:
            with log_path.open('a') as f:
                f.write(f'%s%s' % (
                    '' if log_path.stat().st_size == 0 else '\n',
                    thought.thought
                ))
        finally:
            self.lock.release()

cli = CommandLineInterface()

@cli.command
def run(address, data):
    try:
        ip,port = address.split(':')
        run_server((ip,int(port)), data)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1

def signal_handler(sig, frame):
        print('Exiting...')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    cli.main()
