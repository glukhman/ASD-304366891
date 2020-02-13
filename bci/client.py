from datetime import datetime

import click

from .utils import (Connection, DataReader, Hello, Config, Snapshot,
                    VERSION, DEFAULT_FORMAT)
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

@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
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

def _upload_sample(host, port, path, format):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8000
    if not format:
        format = DEFAULT_FORMAT

    reader_module = __import__('bci.readers', globals(), locals(), [format])
    reader = getattr(reader_module, format).reader_cls(path)
    # generator for reading snapshots from data file
    snapshot_reader = reader.read_snapshot()

    #----------- TODO: debug only -----------
    with reader:
        birthdate = datetime.fromtimestamp(reader.birthdate)
        if format == 'protobuf':
            gender = reader.gender
        else:
            gender = 'male' if reader.gender == b'm' else 'female'
        print(f'user {reader.user_id}: {reader.username}, '
              f'born {birthdate.strftime("%B %-d, %Y")} ({gender})')
    #--------------- end debug ---------------

    connection = Connection.connect(host, port)

    with connection, reader:
        # TODO: cannibalize from <run> above.
        # protocol: while the reader keeps yielding snapshots:
        # 1. send serialized snabshot to run_server
        #    (which includes header = user info + snapshot repacked as protobuf)
        # 2. recieve ack with message size
        pass


# API function aliases
upload_sample = _upload_sample



if __name__ == '__main__':
    cli(prog_name='client')
