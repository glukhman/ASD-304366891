import sys
import json
import logging
from pathlib import Path

import pika
import click
import pymongo
from furl import furl

from .utils import VERSION, TOPICS


def logger_init(name):
    log_dir = Path(__file__).parents[1] / "log"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                        filename=log_dir / f"{name}.log",
                        level=logging.DEBUG)
    logging.getLogger(name).setLevel(logging.DEBUG)
    # raise Exception(log_dir / f"{name}.log")


class Saver:
    def __init__(self, database_url):
        self.database_url = database_url
        database_service = furl(self.database_url).scheme
        if database_service != 'mongodb':
            raise Exception('Unsupported database service')

    def save(self, topic, data):    # data is assumed to arrive in JSON format
        # initialize mongodb
        client = pymongo.MongoClient(self.database_url)
        db = client.db
        table = db[topic]
        # only insert if unique
        try:
            identical_items = list(table.find(json.loads(data)))
            if not identical_items:
                table.insert_one(json.loads(data))
        except json.decoder.JSONDecodeError:
            raise Exception(f"Illegal JSON data format")
        except pymongo.errors.ServerSelectionTimeoutError:
            raise Exception(f"Could not connect to database on URL"
                            f"{self.database_url}")
        message = f"Saved to database table {topic}: {data}".strip('\r\n')
        print(message)
        logging.info(message)


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@click.argument('database-url', required=True)
@click.argument('message-queue-url', required=True)
def run_saver(database_url, message_queue_url):
    logger_init("saver")
    message_queue_url = furl(message_queue_url)
    saver = Saver(database_url)

    # consume parsed data from all topics, then save it to the database
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        message_queue_url.host, message_queue_url.port))
    channel = connection.channel()

    channel.exchange_declare(exchange='parse_results', exchange_type='topic')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    for topic in TOPICS:
        channel.queue_bind(exchange='parse_results', queue=queue_name,
                           routing_key=topic)
    print('Press CTRL+C to exit')

    def callback(ch, method, properties, body):
         # save result to database
         saver.save(method.routing_key, body)

    channel.basic_consume(queue=queue_name, auto_ack=True,
                          on_message_callback=callback)
    channel.start_consuming()


@cli.command()
@click.option('-d', '--database')
@click.argument('topic', required=True)
@click.argument('datapath', required=True)
def save(database, topic, datapath):
    logger_init("saver")
    if not database:
        database = 'mongodb://127.0.0.1:27017'
    saver = Saver(database)
    try:
        with open(datapath, 'r') as f:
            # Load data from data_path. Assumes data is saved in JSON format
            data = f.read()
        saver.save(topic, data)
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        logging.critical(f'{error}')
        return 1


if __name__ == '__main__':
    cli(prog_name='bci.saver')
