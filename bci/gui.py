import json

import click
import requests
import numpy as np
from flask import Flask
from flask import render_template
from flask import send_from_directory
import matplotlib.pyplot as plt, mpld3   # noqa: this is needed for 3D plot
from mpl_toolkits.mplot3d import Axes3D  # noqa: this is needed for 3D plot
from scipy.spatial.transform import Rotation as R
from pathlib import Path

from .utils import VERSION, DATA_DIR


website = Flask(__name__, static_folder='static')


def _html(title, content):
    boilerplate = f"""
    <html>
        <head><title>BCI :: {title}</title></head>
        <body>{content}</body>
    </html>"""
    return boilerplate


@website.route('/')
def index_():

    url = f"http://{website.config['api_host']}:" \
          f"{website.config['api_port']}/users"
    users = sorted(json.loads(requests.get(url).json()),
                   key=lambda item: item['user_id'])
    return render_template('index.html', users=users)


@website.route('/users/<int:user_id>')
def user(user_id):
    host = website.config['api_host']
    port = website.config['api_port']

    url = f"http://{host}:{port}/users/{user_id}"
    user = json.loads(requests.get(url).json())
    url = f"http://{host}:{port}/users/{user_id}/snapshots"
    snapshots = sorted(json.loads(requests.get(url).json()),
                       key=lambda item: item['id'])
    for snapshot in snapshots:
        url = f"http://{host}:{port}/users/{user_id}/snapshots" \
              f"/{snapshot['id']}"
        available_results = json.loads(
            requests.get(url).json())['available results'].split(',')
        available_results = [result.strip() for result in available_results]
        if 'color_image' in available_results:
            url = f"http://{host}:{port}/users/{user_id}/snapshots" \
                  f"/{snapshot['id']}/color_image"
            image_data = json.loads(requests.get(url).json())
            snapshot['image_url'] = image_data['image_url']
        else:
            snapshot['image_url'] = '/static/missing.jpg'
    return render_template('user.html', user=user, snapshots=snapshots)


@website.route('/users/<int:user_id>/snapshots/<string:snapshot_id>')
def snapshot(user_id, snapshot_id):
    host = website.config['api_host']
    port = website.config['api_port']

    url = f"http://{host}:{port}/users/{user_id}"
    user = json.loads(requests.get(url).json())
    url = f"http://{host}:{port}/users/{user_id}/snapshots/{snapshot_id}"
    snapshot = json.loads(requests.get(url).json())
    snapshot['date'], snapshot['time'] = snapshot['datetime'].split('at')
    available_results = json.loads(
        requests.get(url).json())['available results'].split(',')
    available_results = [result.strip() for result in available_results]

    # process color image
    if 'color_image' in available_results:
        url = f"http://{host}:{port}/users/{user_id}/snapshots" \
              f"/{snapshot['id']}/color_image"
        image_data = json.loads(requests.get(url).json())
        snapshot['color_image_url'] = image_data['image_url']
    else:
        snapshot['color_image_url'] = '/static/missing.jpg'

    # process depth image
    if 'depth_image' in available_results:
        url = f"http://{host}:{port}/users/{user_id}/snapshots" \
              f"/{snapshot_id}/depth_image"
        image_data = json.loads(requests.get(url).json())
        snapshot['depth_image_url'] = image_data['image_url']
    else:
        snapshot['depth_image_url'] = '/static/missing.jpg'

    # process pose
    if 'pose' in available_results:
        url = f"http://{host}:{port}/users/{user_id}/snapshots" \
              f"/{snapshot_id}/pose"
        pose = json.loads(requests.get(url).json())

        # translation
        fig = plt.figure(figsize=(12, 12), dpi=72)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim3d(-2, 2)
        ax.set_ylim3d(-2, 2)
        ax.set_zlim3d(-2, 2)

        x = pose['translation']['x']
        y = pose['translation']['y']
        z = pose['translation']['z']
        xline = np.linspace(x, 2, 100)
        yline = np.linspace(-2, y, 100)
        zline = np.linspace(z, 2, 100)
        translation = f'x={x:.2f}, y={y:.2f}, z={z:.2f}'

        ax.scatter(x, y, z, zdir='y', s=1000, c='b', depthshade=True)
        ax.plot(xline, [y]*100, [z]*100, zdir='y', c='b', alpha=0.7, ls='--')
        ax.plot([x]*100, yline, [z]*100, zdir='y', c='b', alpha=0.7, ls='--')
        ax.plot([x]*100, [y]*100, zline, zdir='y', c='b', alpha=0.7, ls='--')

        plt.ylim(plt.ylim()[::-1])
        ax.view_init(elev=20, azim=120)

        datapath = DATA_DIR / 'translations'
        Path(datapath).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{datapath}/{snapshot['id']}.png",
                    bbox_inches='tight', pad_inches=0, dpi=48)
        snapshot['translation_url'] = f"/assets/translations" \
                                      f"/{snapshot['id']}.png"

        # rotation
        fig = plt.figure(figsize=(12, 12), dpi=72)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim3d(-1, 1)
        ax.set_ylim3d(-1, 1)
        ax.set_zlim3d(-1, 1)
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

        ax.plot_surface(x, z, y, color='cyan', lw=1, alpha=0.3)
        ax.plot(np.sin(a), np.cos(a), 0, c='b', alpha=0.3, ls='--')
        ax.plot(np.sin(b), np.cos(b), 0, c='b', alpha=0.7)
        ax.plot([0]*100, np.sin(v), np.cos(v), c='b', alpha=0.7)
        ax.plot([0]*100, np.sin(c), np.cos(c), c='b', alpha=0.3, ls='--')

        rotation = [pose['rotation']['x'], pose['rotation']['y'],
                    pose['rotation']['z'], pose['rotation']['w']]

        rotation_vector = R.from_quat(rotation)
        vector = rotation_vector.apply([0, 1, 0])
        vector[1] = -vector[1]  # invert depth axis

        ax.quiver(0, 0, 0, *vector, length=1, linewidth=5, color='k')
        ax.view_init(elev=20, azim=120)

        datapath = DATA_DIR / 'rotations'
        Path(datapath).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{datapath}/{snapshot['id']}.png",
                    bbox_inches='tight', pad_inches=0, dpi=48)
        snapshot['rotation_url'] = f"/assets/rotations/{snapshot['id']}.png"

        x, y, z, w = rotation
        rotation = f'x={x:.2f}, y={y:.2f}, z={z:.2f}, w={w:.2f}'
    else:
        translation = ''
        rotation = ''
        snapshot['translation_url'] = '/static/missing.jpg'
        snapshot['rotation_url'] = '/static/missing.jpg'

    template_html = 'snapshot.html'

    # process feelings
    if 'feelings' in available_results:
        url = f"http://{host}:{port}/users/{user_id}/snapshots" \
              f"/{snapshot_id}/feelings"
        feelings = json.loads(requests.get(url).json())
        template_html = 'snapshot_with_feelings.html'
        hunger = "{0:.1f}".format(feelings['hunger'] * 100)
        thirst = "{0:.1f}".format(feelings['thirst'] * 100)
        exhaustion = "{0:.1f}".format(feelings['exhaustion'] * 100)
        happiness = "{0:.1f}".format(feelings['happiness'] * 100)
    else:
        hunger, thirst, exhaustion, happiness = 0, 0, 0, 0

    return render_template(template_html, user=user, snapshot=snapshot,
                           hunger=hunger, thirst=thirst, exhaustion=exhaustion,
                           happiness=happiness, translation=translation,
                           rotation=rotation)


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
    website.TEMPLATES_AUTO_RELOAD = True
    website.run(host, port)


# API function aliases
run_server = _run_server    # noqa

if __name__ == '__main__':
    cli(prog_name='REST api')
