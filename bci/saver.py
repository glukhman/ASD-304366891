import json

import pika
import click
import pymongo
from furl import furl

from .utils import VERSION, TOPICS


class Saver:
    def __init__(self, database_url):
        database_url = furl(database_url)
        self.database = database_url.scheme
        self.host = database_url.host
        self.port = database_url.port
        if self.database != 'mongodb':
            raise Exception('Unsupported database service')

        # TODO: initialize the appropriate db client at init (??)

    def save(self, topic, data):    # data is assumed to arrive in JSON format

        # initialize db
        client = pymongo.MongoClient()
        db = client.db
        table = db[topic]
        result = table.insert_one(json.loads(data))

        # DEBUG check:
        print(table.find_one({'_id': result.inserted_id}))


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@click.argument('database-url', required=True)
@click.argument('message-queue-url', required=True)
def run_saver(database_url, message_queue_url):
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
    print(' [*] Waiting for logs. To exit press CTRL+C')

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
    if not database:
        database = 'mongodb://127.0.0.1:27017'
    saver = Saver(database)
    try:
        with open(datapath, 'r') as f:
            # Load data from data_path. Assumes data is saved in JSON format
            data = f.read()
            saver.save(topic, data)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


if __name__ == '__main__':
    cli(prog_name='saver')
