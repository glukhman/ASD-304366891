import socket

class Connection:
    def __init__(self, socket):
        self.socket = socket

    def __repr__(self):
        return f'<Connection from %s to %s>' % (
            ':'.join(str(arg) for arg in self.socket.getsockname()),
            ':'.join(str(arg) for arg in self.socket.getpeername()),
        )
    def __enter__(self):
        pass

    def __exit__(self, exception, error, traceback):
        self.close()

    def send(self, data):
        self.socket.sendall(data)

    def receive(self, size):
        data = self.socket.recv(size)
        if len(data) != size:
            raise Exception('data is incomplete')
        return data

    def close(self):
        self.socket.close()

    @classmethod
    def connect(cls, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return Connection(sock)
