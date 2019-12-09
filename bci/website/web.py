from pathlib import Path
from flask import Flask, abort

website = Flask(__name__)
data_dir = None

def run_webserver(address, data):
    try:
        global data_dir
        data_dir = data
        ip,port = address
        website.run(ip,int(port))
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
    return _html('', content)

@website.route('/users/<int:user_id>')
def user(user_id):
    users_list = [f.name for f in Path(data_dir).glob('*') if f.is_dir()]
    if str(user_id) not in users_list:
        abort(404)
    files_list = Path(data_dir, str(user_id)).glob('*.txt')
    content = []
    for file in sorted(files_list):
        timestamp = file.name.split('.')[0].split('_')
        timestamp = '{0} {1}'.format(timestamp[0], timestamp[1].replace('-',':'))
        thought = file.read_text()
        content.append(f'<tr><td>{timestamp}</td><td>{thought}</td></tr>')
    content = '<table>{0}</table>'.format(''.join(content))
    return _html(f': User {user_id}', content)
