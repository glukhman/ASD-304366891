import struct
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

    def send_message(self, message):
        if type(message) == str:
            message = message.encode('utf8')
        msg_size = len(message)    # data should be binary

        msg_header = struct.pack('<I', msg_size)
        self.socket.sendall(msg_header + message)

    def receive(self, size):
        data = self.socket.recv(size)
        if len(data) != size:
            raise Exception('data is incomplete')
        return data

    def receive_message(self):
        msg_size = self.socket.recv(4)
        msg_size, = struct.unpack('<I', msg_size)
        data = bytes()
        while len(data) < msg_size:
            new_data = self.socket.recv(1024)
            if not new_data:
                break
            data += new_data
        if len(data) != msg_size:
            raise Exception('data is incomplete')
        return data

    def close(self):
        self.socket.close()

    @classmethod
    def connect(cls, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return Connection(sock)
