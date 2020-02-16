import click
import requests
from flask import Flask
# from flask_restful import Resource, Api

from .utils import VERSION


website = Flask(__name__)


def _html(title, content):
    boilerplate = f"""
    <html>
        <head><title>BCI :: {title}</title></head>
        <body>{content}</body>
    </html>"""
    return boilerplate


@website.route('/')
def index_():
    url = f"http://{website.config['api_host']}:{website.config['api_port']}/users"
    content = requests.get(url).text
    # users_list = [f.name for f in Path(data_dir).glob('*') if f.is_dir()]
    # users_list = [f'<li><a href="/users/{f}">user {f}</a></li>'
    #               for f in users_list]
    # content = '<ul>{0}</ul>'.format(''.join(sorted(users_list)))
    return _html('Welcome', content)


@click.version_option(prog_name='Michael Glukhman\'s BCI', version=VERSION)
@click.group()
def cli():
    pass


@cli.command()
@click.option('-h', '--host')
@click.option('-p', '--port', type=int)
@click.option('-H', '--api-host')
@click.option('-P', '--api-port', type=int)
def run_server(host, port, api_host, api_port):
    try:
        _run_server(host, port, api_host, api_port)
    except Exception as error:
        print(f'ERROR: {error}')
        return 1


def _run_server(host, port, api_host, api_port):
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 8080
    if not api_host:
        api_host = '127.0.0.1'
    if not api_port:
        api_port = 8000
    website.config['api_host'] = api_host
    website.config['api_port'] = api_port
    website.run(host, port)


# API function aliases
run_server = _run_server

if __name__ == '__main__':
    cli(prog_name='REST api')
