import click
from . import client, server
from .website import web
from .utils import reader

VERSION = 0.5


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@click.argument('address')
@click.argument('user', type=int)
@click.argument('thought')
def upload_thought(address, user, thought):
    try:
        ip, port = address.split(':')
        client.upload_thought((ip, int(port)), int(user), thought)
        print('done')
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


@cli.command()
@click.argument('port')
@click.argument('datapath', required=False)
def run_server(port, datapath):
    if not datapath:
        datapath = 'data'
    try:
        server.run(port, datapath)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


@cli.command()
@click.argument('filepath')
@click.argument('port')
def run_client(filepath, port):
    client.run(filepath, port)


@cli.command()
@click.argument('address')
@click.argument('data')
def run_web(address, data):
    web.run_webserver(address.split(":"), data)


@cli.command()
@click.argument('filepath')
def read(filepath):
    reader.read(filepath)


if __name__ == '__main__':
    cli(prog_name='bci')
