import json
import click
import requests
from tabulate import tabulate

from .utils import VERSION


def common_options(f):
    options = [
        click.option('-h', '--host'),
        click.option('-p', '--port', type=int)
    ]

    def check_host_port(host=None, port=None, *args, **kwargs):
        if not host:
            host = '127.0.0.1'
        if not port:
            port = 8000
        return f(host, port, *args, **kwargs)

    for option in reversed(options):
        check_host_port = option(check_host_port)
    check_host_port.__name__ = f.__name__
    return check_host_port


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@common_options
def get_users(host, port):
    try:
        url = f'http://{host}:{port}/users'
        response = json.loads(requests.get(url).json())
        headers = list(response[0].keys())
        items = [list(item.values()) for item in response]
        print(tabulate(items, headers=headers, tablefmt="grid"))
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


@cli.command()
@click.argument('user-id', required=True)
@common_options
def get_user(host, port, user_id):
    try:
        url = f'http://{host}:{port}/users/{user_id}'
        response = json.loads(requests.get(url).json())
        items = [[item[0]+":", item[1]] for item in response.items()]
        print(f'\nUser {user_id}\'s data\n{"-"*25}')
        print(tabulate(items, tablefmt="plain"), '\n')
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


@cli.command()
@click.argument('user-id', required=True)
@common_options
def get_snapshots(host, port, user_id):
    try:
        url = f'http://{host}:{port}/users/{user_id}/snapshots'
        response = json.loads(requests.get(url).json())
        headers = list(response[0].keys())
        items = [list(item.values()) for item in response]
        print(f'\nSnapshots taken by user {user_id}:')
        print(tabulate(items, headers=headers, tablefmt="grid"))
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


@cli.command()
@click.argument('user-id', required=True)
@click.argument('snapshot-id', required=True)
@common_options
def get_snapshot(host, port, user_id, snapshot_id):
    try:
        url = f'http://{host}:{port}/users/{user_id}/snapshots/{snapshot_id}'
        response = json.loads(requests.get(url).json())
        items = [[item[0]+":", item[1]] for item in response.items()]
        print(f'\nSnapshot {snapshot_id} taken by user {user_id}:\n{"-"*40}')
        print(tabulate(items, tablefmt="plain"), '\n')
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


@cli.command()
@click.argument('user-id', required=True)
@click.argument('snapshot-id', required=True)
@click.argument('result-name', required=True)
@common_options
def get_result(host, port, user_id, snapshot_id, result_name):
    try:
        url = f'http://{host}:{port}/users/{user_id}/snapshots/' \
              f'{snapshot_id}/{result_name}'
        response = json.loads(requests.get(url).json())
        items = [[item[0]+":", item[1]] for item in response.items()]
        print(f'\n{result_name.upper()} of snapshot {snapshot_id} taken by '
              f'user {user_id}:\n{"-"*50}')
        print(tabulate(items, tablefmt="plain"), '\n')
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


if __name__ == '__main__':
    cli(prog_name='bci.cli')
