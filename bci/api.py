import json

import click
import pymongo
from furl import furl
from flask import Flask
from flask_restful import Resource, Api

from .utils import VERSION, SNAPSHOT_TOPICS


app = Flask(__name__)
api = Api(app)
api_database = None


class Users(Resource):
    def get(self):
        client = pymongo.MongoClient(app.config['database_url'])
        table = client.db['users']
        results = list(table.find({}, {'user_id': 1, 'username': 1}))
        for result in results:
            del result['_id']   # purge the non-serializable _id key
        return json.dumps(results), 200


class UserData(Resource):
    def get(self, user_id):
        client = pymongo.MongoClient(app.config['database_url'])
        table = client.db['users']
        result = table.find_one({'user_id': int(user_id)})
        del result['_id']   # purge the non-serializable _id key
        return json.dumps(result), 200


class Snapshots(Resource):
    def get(self, user_id):
        client = pymongo.MongoClient(app.config['database_url'])
        table = client.db['snapshots']
        results = list(table.find({'user_id': int(user_id)},
                                  {'id': 1, 'datetime': 1}))
        for result in results:
            del result['_id']   # purge the non-serializable _id key
        return json.dumps(results), 200


class SnapshotData(Resource):
    def get(self, user_id, snapshot_id):
        client = pymongo.MongoClient(app.config['database_url'])
        table = client.db['snapshots']
        result = table.find_one({'user_id': int(user_id),
                                 'id': int(snapshot_id)},
                                {'id': 1, 'datetime': 1})
        del result['_id']   # purge the non-serializable _id key

        available_results = []
        for topic in SNAPSHOT_TOPICS:
            table = client.db[topic]
            has_topic = table.find_one({'id': int(snapshot_id)})
            if has_topic:
                available_results.append(topic)
        result['available results'] = ', '.join(available_results)
        return json.dumps(result), 200


class SnapshotResults(Resource):
    def get(self, user_id, snapshot_id, result_name):
        client = pymongo.MongoClient(app.config['database_url'])
        table = client.db[result_name]
        result = table.find_one({'user_id': int(user_id),
                                 'id': int(snapshot_id)})
        del result['_id']   # purge the non-serializable _id key
        del result['id']        # get rid of redundant fields
        del result['user_id']
        return json.dumps(result), 200


api.add_resource(Users, '/users')
api.add_resource(UserData, '/users/<string:user_id>')
api.add_resource(Snapshots, '/users/<string:user_id>/snapshots')
api.add_resource(SnapshotData, '/users/<string:user_id>/snapshots/<string:snapshot_id>')
api.add_resource(SnapshotResults, '/users/<string:user_id>/snapshots/<string:snapshot_id>/<string:result_name>')


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@click.option('-h', '--host')
@click.option('-p', '--port', type=int)
@click.option('-d', '--database')
def run_server(host, port, database):
    try:
        run_api_server(host, port, database)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


def run_api_server(host, port, database_url):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8000
    if not database_url:
        database_url = 'mongodb://127.0.0.1:27017'
    global api_database
    app.config['database_url'] = database_url
    app.run(host, port)


if __name__ == '__main__':
    cli(prog_name='bci.api')
