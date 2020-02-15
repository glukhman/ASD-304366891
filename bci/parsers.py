import json
from pathlib import Path
from datetime import datetime

import pika
import click
from furl import furl

from .utils import VERSION, DATA_DIR, MSG_TYPES
from .utils.protobuf import cortex_pb2


class BasicParser:
    def __init__(self):
        self.snapshot = None

    def parse(self, raw_snapshot_path):
        # read from raw file and unpack using protobuf3
        datapath = Path(raw_snapshot_path)
        self.snapshot = cortex_pb2.Snapshot()

        with open(datapath, 'rb') as f:
            self.snapshot.ParseFromString(f.read())


# Final project
@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass

@cli.command()
@click.argument('parser', required=True)
@click.argument('message-queue-url', required=True)
def run_parser(parser, message_queue_url):
    # retrieve publisher module
    message_queue_url = furl(message_queue_url)
    publisher = __import__(f'bci.publishers.{message_queue_url.scheme}',
                           globals(),
                           locals(),
                           [message_queue_url.scheme])
    try:
        _run_parser(parser, publish=publisher,
                    publisher_host=message_queue_url.host,
                    publisher_port=message_queue_url.port)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


def _run_parser(parser, publish, **kwargs):
    if (not kwargs['publisher_host']) or (not kwargs['publisher_port']):
        raise Exception('no host or port provided for parser service')

    # retrieve parser class
    parser_module = __import__('bci.parsing', globals(), locals(), [parser])
    parser = getattr(parser_module, parser).parser_cls()

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        kwargs['publisher_host'], kwargs['publisher_port']))
    channel = connection.channel()

    channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='raw_snapshot', queue=queue_name)
    print(' [*] Waiting for logs. To exit press CTRL+C')
    def callback(ch, method, properties, body):
        parser.parse(body.decode())
    channel.basic_consume(queue=queue_name,
                          auto_ack=True,
                          on_message_callback=callback)
    channel.start_consuming()


@cli.command()
@click.argument('parser', required=True)
@click.argument('raw-data-path', required=True)
def parse(parser, raw_data_path):
    # retrieve parser class
    parser_module = __import__('bci.parsing', globals(), locals(), [parser])
    parser = getattr(parser_module, parser).parser_cls()
    try:
        parser.parse(raw_data_path)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


# API function aliases
run_parser = _run_parser

if __name__ == '__main__':
    cli(prog_name='bci.parsers')
