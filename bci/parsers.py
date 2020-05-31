import sys
import json
import logging
from pathlib import Path

import pika
import click
from furl import furl

from .utils import VERSION
from .utils.protobuf import cortex_pb2


def logger_init(name):
    log_dir = Path(__file__).parents[1] / "log"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                        filename=log_dir / f"{name}.log",
                        level=logging.DEBUG)
    logging.getLogger(name).setLevel(logging.DEBUG)
    logging.getLogger("pika").propagate = False


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
    logger_init('parsers')
    # retrieve publisher module
    message_queue_url = furl(message_queue_url)
    try:
        publisher = __import__(f'bci.publishers.{message_queue_url.scheme}',
                               globals(),
                               locals(),
                               [message_queue_url.scheme])
    except ModuleNotFoundError:
        error = f'Publisher module "{message_queue_url.scheme}" does not exist'
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1

    try:
        _run_parser(parser, publish=publisher,
                    publisher_host=message_queue_url.host,
                    publisher_port=message_queue_url.port)
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1


def _run_parser(parser, publish, **kwargs):
    if (not kwargs['publisher_host']) or (not kwargs['publisher_port']):
        error_msg = 'no host or port provided for publisher service'
        # logging.critical(f'[{parser}] {error_msg}')
        raise Exception(f'[{parser}] {error_msg}')

    # retrieve parser class
    try:
        parser_module = __import__('bci.parsing', globals(), locals(),
                                   [parser])
        parser_engine = getattr(parser_module, parser).parser_cls()
    except ModuleNotFoundError:
        error = f'Parsing module "{parser_module}" does not exist'
        raise Exception(f'[{parser}] {error_msg}')

    # check and establish connection
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            kwargs['publisher_host'], kwargs['publisher_port']))
    except pika.exceptions.AMQPConnectionError:
        error_msg = f"could not connect to rabbitmq through host " \
                    f"{kwargs['publisher_host']} and port " \
                    f"{kwargs['publisher_port']}"
        raise Exception(f'[{parser}] {error_msg}')

    # consume raw snapshot messages, then parse them and publish to
    # dedicated topics
    channel = connection.channel()

    channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='raw_snapshot', queue=queue_name)
    print('Press CTRL+C to exit')

    def callback(ch, method, properties, body):
        # parse raw data
        body = json.loads(body)
        parse_result = parser_engine.parse(body['address'])

        # append user id to parsed data
        parse_result = json.loads(parse_result)
        parse_result['user_id'] = body['user_id']
        parse_result = json.dumps(parse_result)

        # publish to saver
        save_channel = connection.channel()
        save_channel.exchange_declare(exchange='parse_results',
                                      exchange_type='topic')
        routing_key = parser
        save_channel.basic_publish(exchange='parse_results',
                                   routing_key=routing_key, body=parse_result)
        logging.info(f'Sent to {routing_key} topic: {parse_result}')

    channel.basic_consume(queue=queue_name, auto_ack=True,
                          on_message_callback=callback)
    channel.start_consuming()


@cli.command()
@click.argument('parser', required=True)
@click.argument('raw-data-path', required=True)
def parse(parser, raw_data_path):
    _parse(parser, raw_data_path)


def _parse(parser, raw_data_path):
    logger_init('parsers')
    # retrieve parser class
    try:
        parser_module = __import__('bci.parsing', globals(), locals(),
                                   [parser])
        parser_name = parser
        parser = getattr(parser_module, parser).parser_cls()
        result = parser.parse(raw_data_path)
        print(result)
        logging.info(f'[{parser_name}] {result}')
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'[{parser_name}] {error}')
        return 1


# API function aliases
run_parser = _parse # noqa

if __name__ == '__main__':
    cli(prog_name='bci.parsers')
