import json

import click
import requests
import numpy as np
from flask import Flask
from flask import send_from_directory
import matplotlib.pyplot as plt, mpld3
from mpl_toolkits.mplot3d import Axes3D
import pytransform3d.rotations as pr
from tabulate import tabulate
from pathlib import Path

from .utils import VERSION, DATA_DIR


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
    users_list = json.loads(requests.get(url).json())
    users_list = ['<li><a href="/users/{0}">{1}</a></li>'.format(
            user['user_id'], user['username']
        ) for user in users_list]
    content = '<h1>Users</h1><ul>{}</ul>'.format(''.join(sorted(users_list)))
    return _html('Welcome', content)


@website.route('/users/<int:user_id>')
def user(user_id):
    url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}"
    user_data = json.loads(requests.get(url).json())
    username = user_data['username']
    content = f"<h1>{username}</h1>{user_data['gender'].capitalize()}. Born on {user_data['birthday']}"
    content += f"<h3>{username}'s snapshots:</h3>"

    url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}/snapshots"
    snapshots = json.loads(requests.get(url).json())

    snapshots = ['<li><a href="/users/{0}/snapshots/{1}">{1}</a>&emsp;taken on {2}</li>'.format(
            user_id, snapshot['id'], snapshot['datetime']
        ) for snapshot in snapshots]
    content += '<ul>{}</ul>'.format(''.join(sorted(snapshots)))
    content += '<a href="/">Back</a>'
    return _html(f'User {user_id}', content)


@website.route('/users/<int:user_id>/snapshots/<string:snapshot_id>')
def snapshot(user_id, snapshot_id):
    url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}"
    user_data = json.loads(requests.get(url).json())
    url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}/snapshots/{snapshot_id}"
    snapshot_data = json.loads(requests.get(url).json())
    print(snapshot_data)
    content = f"<h1>Snapshot by {user_data['username']}</h1>"
    content += f"Snapshot #{snapshot_data['id']} taken at {snapshot_data['datetime']}"

    available_results = snapshot_data['available results'].split(',')
    available_results = [result.strip() for result in available_results]

    # show color image
    if 'color_image' in available_results:
        url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}/snapshots/{snapshot_id}/color_image"
        image_data = json.loads(requests.get(url).json())
        print(image_data)
        content += f"<p><img src='{image_data['image_url']}' alt='Color image' width='50%'>"

    # show depth image
    if 'depth_image' in available_results:
        url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}/snapshots/{snapshot_id}/depth_image"
        image_data = json.loads(requests.get(url).json())
        print(image_data)
        content += f"<p><img src='{image_data['image_url']}' alt='Depth image' width='30%'>"

    # show pose
    if 'pose' in available_results:
        url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}/snapshots/{snapshot_id}/pose"
        pose_data = json.loads(requests.get(url).json())

        # translation
        fig = plt.figure(figsize=(12,12), dpi=72)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim3d(-2,2)
        ax.set_ylim3d(-2,2)
        ax.set_zlim3d(-2,2)

        x = pose_data['translation']['x']
        y = pose_data['translation']['y']
        z = pose_data['translation']['z']
        xline = np.linspace(x, 2, 100)
        yline = np.linspace(-2, y, 100)
        zline = np.linspace(-2, z, 100)

        ax.scatter(x, y, z, zdir='z', s=1000, c='b', depthshade=True)
        ax.plot(xline, [y]*100, [z]*100, c='b', alpha=0.7, ls='--')
        ax.plot([x]*100, yline, [z]*100, c='b', alpha=0.7, ls='--')
        ax.plot([x]*100, [y]*100, zline, c='b', alpha=0.7, ls='--')

        ax.view_init(elev = 20, azim = 120)

        datapath = DATA_DIR / 'translations'
        Path(datapath).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{datapath}/{snapshot_data['id']}.png",
                    bbox_inches='tight', pad_inches=0, dpi=48)
        content += f"<p><img src='/assets/translations/{snapshot_data['id']}.png' alt='Translation plot'>"

        # rotation
        fig = plt.figure(figsize=(12,12), dpi=72)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim3d(-1,1)
        ax.set_ylim3d(-1,1)
        ax.set_zlim3d(-1,1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])

        a = np.linspace(.33*np.pi, 1.33*np.pi, 100)
        b = np.linspace(-.67*np.pi, .33*np.pi, 100)
        c = np.linspace(np.pi, 2*np.pi, 100)
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x = np.outer(np.cos(u), np.sin(v))
        y = np.outer(np.sin(u), np.sin(v))
        z = np.outer(np.ones(np.size(u)), np.cos(v))

        ax.plot_surface(x, y, z, color='cyan', lw=1, alpha=0.3)
        ax.plot(np.sin(a), np.cos(a), 0, c='b', alpha=0.3, ls='--')
        ax.plot(np.sin(b), np.cos(b), 0, c='b', alpha=0.7)
        ax.plot([0]*100, np.sin(v), np.cos(v), c='b', alpha=0.7)
        ax.plot([0]*100, np.sin(c), np.cos(c), c='b', alpha=0.3,
                ls='--')

        rotation = [pose_data['rotation']['x'], pose_data['rotation']['y'],
                    pose_data['rotation']['z'], pose_data['rotation']['w']]
        vector = pr.q_prod_vector(np.array(rotation),
                                  np.array([0,0,1]))
        ax.quiver(0,0,0,*vector, length=1, linewidth=5,color='k')
        ax.view_init(elev = 20, azim = 120)

        datapath = DATA_DIR / 'rotations'
        Path(datapath).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{datapath}/{snapshot_data['id']}.png",
                    bbox_inches='tight', pad_inches=0, dpi=48)
        content += f"<p><img src='/assets/rotations/{snapshot_data['id']}.png' alt='Rotation plot'>"

    # show feelings
    if 'feelings' in available_results:
        url = f"http://{website.config['api_host']}:{website.config['api_port']}/users/{user_id}/snapshots/{snapshot_id}/feelings"
        feelings_data = json.loads(requests.get(url).json())
        content += f"<p>{feelings_data}"

    content += f"<p><a href='/users/{user_id}'>Back to {user_data['username']}'s page</a>"
    return _html(f'Snapshot', content)


@website.route('/assets/<string:type>/<string:asset_id>')
def get_asset(type, asset_id):
    return send_from_directory(DATA_DIR / type, asset_id, as_attachment=True)


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
