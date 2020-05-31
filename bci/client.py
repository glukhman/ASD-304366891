import sys
import logging
from pathlib import Path

import click

from .utils import (Connection, UserData, Snapshot, VERSION, DEFAULT_FORMAT)


def logger_init(name):
    log_dir = Path(__file__).parents[1] / "log"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                        filename=log_dir / f"{name}.log",
                        level=logging.DEBUG)
    logging.getLogger(name).setLevel(logging.DEBUG)


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
    logger_init('client')
    try:
        _upload_sample(host, port, path, format)
    except Exception as error:
        if 'Temporary failure in name resolution' in str(error):
            error = f'unknown host name "{host}"'
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1


def _upload_sample(host, port, path, format=None):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 5000
    if not format:
        format = DEFAULT_FORMAT

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
            if 'ERROR' in ack_msg.decode():
                print(f'User data: {ack_msg.decode()}', file=sys.stderr)
                logging.warning(f'{ack_msg.decode()}')
            else:
                print(f'User data: {ack_msg.decode()}')
                logging.info(f'User data: {ack_msg.decode()}')

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
                if 'ERROR' in ack_msg.decode():
                    print(f'Snapshot #{i}: {ack_msg.decode()}',
                          file=sys.stderr)
                    logging.warning(f'{ack_msg.decode()}')
                else:
                    print(f'Snapshot #{i}: {ack_msg.decode()}')
                    logging.info(f'Snapshot #{i}: {ack_msg.decode()}')
            i += 1


# API function aliases
upload_sample = _upload_sample  # noqa

if __name__ == '__main__':
    cli(prog_name='bci.client')
