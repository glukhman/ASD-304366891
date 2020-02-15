from datetime import datetime

import click

from .utils import (Connection, UserData, Snapshot, VERSION, DEFAULT_FORMAT)
from .thought import Thought


def upload_thought(address, user_id, thought):
    connection = Connection.connect(*address)
    with connection:
        thought = Thought(user_id, datetime.now(), thought)
        connection.send(thought.serialize())

# EX-6
def run(filepath, port):
    connection = Connection.connect('127.0.0.1', int(port))
    reader = DataReader(filepath)
    # generator for reading snapshots from data file
    snapshot_reader = reader.read_snapshot()

    with connection, reader:

        # send hello message to server
        hello_msg = Hello(reader.user_id, reader.username,
                          reader.birthdate, reader.gender)
        connection.send_message(hello_msg.serialize())

        # receive config message from server
        config_msg = connection.receive_message()
        config_msg = Config.deserialize(config_msg)

        # send snapshot to server
        reader.set_config_fields(config_msg.config_fields)
        snapshot_msg = Snapshot(snapshot_reader)
        connection.send_message(snapshot_msg.serialize())

# Final project
@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass

@cli.command()
@click.option('-h', '--host')
@click.option('-p', '--port', type=int)
@click.argument('path')
@click.option('-f', '--format')
def upload_sample(host, port, path, format):
    try:
        _upload_sample(host, port, path)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1

def _upload_sample(host, port, path, format=DEFAULT_FORMAT):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8000

    reader_module = __import__('bci.readers', globals(), locals(), [format])
    reader = getattr(reader_module, format).reader_cls(path)
    # generator for reading snapshots from data file
    snapshot_reader = reader.read_snapshot()

    # send user data to server + receive ack message from server
    connection = Connection.connect(host, port)
    with connection, reader:

        user_data = UserData(reader)
        packed_user_data = user_data.serialize()
        connection.send_message(packed_user_data)

        ack_msg = connection.receive_message()
        print(f'User data: {ack_msg.decode()}')

    # send snapshot to server + receive ack message from server
    connection = Connection.connect(host, port)
    with connection, reader:
        snapshot = Snapshot(user_data.user_id, snapshot_reader)
        packed_snapshot = snapshot.serialize()
        connection.send_message(packed_snapshot)

        # receive ack message from server
        ack_msg = connection.receive_message()
        print(f'Snapshot #{1}: {ack_msg.decode()}')


# API function aliases
upload_sample = _upload_sample

if __name__ == '__main__':
    cli(prog_name='client')
