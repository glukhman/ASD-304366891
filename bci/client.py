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
        _upload_sample(host, port, path, format)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


def _upload_sample(host, port, path, format=None):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8000
    if not format:
        format=DEFAULT_FORMAT

    reader_module = __import__('bci.readers', globals(), locals(), [format])
    reader = getattr(reader_module, format).reader_cls(path)
    with reader:

        # generator for reading snapshots from data file
        snapshot_reader = reader.read_snapshot()

        # send user data to server + receive ack message from server
        connection = Connection.connect(host, port)
        with connection:

            user_data = UserData(reader)
            packed_user_data = user_data.serialize()
            connection.send_message(packed_user_data)

            ack_msg = connection.receive_message()
            print(f'User data: {ack_msg.decode()}')

        # send snapshot to server + receive ack message from server
        i = 1
        while True:
            connection = Connection.connect(host, port)
            with connection:
                try:
                    snapshot = Snapshot(user_data.user_id,
                               next(snapshot_reader))
                except StopIteration:
                    break
                packed_snapshot = snapshot.serialize()
                connection.send_message(packed_snapshot)

                # receive ack message from server
                ack_msg = connection.receive_message()
                print(f'Snapshot #{i}: {ack_msg.decode()}')
            i += 1


# API function aliases
upload_sample = _upload_sample

if __name__ == '__main__':
    cli(prog_name='client')
