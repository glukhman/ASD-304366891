from ..cli import CommandLineInterface
from .website import Website
from pathlib import Path
import signal, sys

cli = CommandLineInterface()
website = Website()
data_dir = None

def signal_handler(sig, frame):
        print('Exiting...')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

@cli.command
def run(address, data):
    run_webserver(address.split(":"), data)

def run_webserver(address, data):
    try:
        global data_dir
        data_dir = data
        ip,port = address
        website.run((ip,int(port)))
    except Exception as error:
        print(f'ERROR: {error}')
        return 1

def _html(title, content):
    boilerplate = f"""
    <html>
        <head><title>Brain Computer Interface{title}</title></head>
        <body>{content}</body>
    </html>"""
    return boilerplate

@website.route('/')
def index_():
    users_list = [f.name for f in Path(data_dir).glob('*') if f.is_dir()]
    users_list = [f'<li><a href="/users/{f}">user {f}</a></li>' for f in users_list]
    content = '<ul>{0}</ul>'.format(''.join(sorted(users_list)))
    return 200, _html('', content)

@website.route('/users/([0-9]+)')
def user(user_id):
    users_list = [f.name for f in Path(data_dir).glob('*') if f.is_dir()]
    if str(user_id) not in users_list:
        return 404, ''
    files_list = Path(data_dir, user_id).glob('*.txt')
    content = []
    for file in sorted(files_list):
        timestamp = file.name.split('.')[0].split('_')
        timestamp = '{0} {1}'.format(timestamp[0], timestamp[1].replace('-',':'))
        thought = file.read_text()
        content.append(f'<tr><td>{timestamp}</td><td>{thought}</td></tr>')
    content = '<table>{0}</table>'.format(''.join(content))
    return 200, _html(f': User {user_id}', content)

if __name__ == '__main__':
    cli.main()
