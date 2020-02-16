from datetime import datetime

import click

from .utils import (Connection, UserData, Snapshot, VERSION, DEFAULT_FORMAT)


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
