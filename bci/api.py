import json

import click
import pymongo
from furl import furl
from flask import Flask
from flask_restful import Resource, Api

from .utils import VERSION, TOPICS


app = Flask(__name__)
api = Api(app)
api_database = None


class Users(Resource):
    def get(self):
        return f"list all registered users; database: {app.config['database_url']}"


class SnapshotResults(Resource):
    def get(self, user_id, snapshot_id, result_name):
        return {'hello': 'world'}, 201

api.add_resource(Users, '/users')
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
    cli(prog_name='REST api')
