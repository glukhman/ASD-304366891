import socket, struct
from datetime import datetime
from .cli import CommandLineInterface
from .utils.connection import Connection
from .thought import Thought

def upload_thought(address, user_id, thought):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(address)
    connection = Connection(sock)
    thought = Thought(user_id, datetime.now(), thought)
    connection.send(thought.serialize())

cli = CommandLineInterface()

@cli.command
def upload(address, user, thought):
    try:
        ip,port = address.split(':')
        upload_thought((ip,int(port)), int(user), thought)
        print('done')
    except Exception as error:
        print(f'ERROR: {error}')
        return 1

if __name__ == '__main__':
    cli.main()
