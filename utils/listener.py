from connection import Connection
import socket

class Listener:
    def __init__(self, /, port, host='0.0.0.0', backlog=1000, reuseaddr=True):
        self.port, self.host, self.backlog, self.reuseaddr  = port, host, backlog, reuseaddr

    def __repr__(self):
        return f'Listener(port={self.port}, host=\'{self.host}\', backlog={self.backlog}, reuseaddr={self.reuseaddr})'

    def __enter__(self):
        self.start()

    def __exit__(self, exception, error, traceback):
        self.stop()

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.reuseaddr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.backlog)   # max. connections

    def stop(self):
        self.socket.close()

    def accept(self):
        connection, _ = self.socket.accept()
        return Connection(connection)
