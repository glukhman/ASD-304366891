import click
import requests

from .utils import VERSION, TOPICS


def common_options(f):
    options = [
        click.option('-h', '--host'),
        click.option('-p', '--port', type=int)
    ]
    def check_host_port(host=None, port=None):
        if not host:
            host = '127.0.0.1'
        if not port:
            port = 8000
        return f(host, port)
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
        response = requests.get(url)
        print(response.status_code, response.text)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


if __name__ == '__main__':
    cli(prog_name='CLI')
