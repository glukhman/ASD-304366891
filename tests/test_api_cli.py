import requests
from click.testing import CliRunner

from bci.cli import (get_users, get_user, get_snapshots,
                     get_snapshot, get_result)
from conftest import capture


class MockResponse:
    def __init__(self, entrypoint):
        self.entrypoint = entrypoint

    def json(self):
        if self.entrypoint == 'users':
            return '[{"user_id": 123, "username": "Testy"}, {"user_id": 456}]'
        if self.entrypoint == 'users/123':
            return '{"user_id": 123, "username": "Testy", "gender": "male"}'
        if self.entrypoint == 'users/123/snapshots':
            return '[{"id": 123456789, "datetime": "April 1, 2019"}, ' \
                   '{"id": 123456889, "datetime": "April 2, 2019"}]'
        if self.entrypoint == 'users/123/snapshots/123456789':
            return '{"id": 123456789, "datetime": "April 1, 2019", ' \
                   '"available results": "pose, feelings"}'
        if self.entrypoint == 'users/123/snapshots/123456789/pose':
            return '{"translation": {"x": 0, "y": 0, "z": -1}, ' \
                   '"rotation": {"x": -0.5, "y": 0.33, "z": 0, "w": 0.15}}'


def test_get_users(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse('users')
    runner = CliRunner()
    monkeypatch.setattr(requests, "get", mock_get)

    result = runner.invoke(get_users)
    assert "|   user_id | username   |" in result.output
    assert "|       123 | Testy      |" in result.output
    assert "|       456 |            |" in result.output


def test_get_user(monkeypatch):
    user_id = '123'

    def mock_get(*args, **kwargs):
        return MockResponse(f'users/{user_id}')

    runner = CliRunner()
    monkeypatch.setattr(requests, "get", mock_get)

    result = runner.invoke(get_user, [user_id])
    assert "User 123's data" in result.output
    assert "user_id:   123" in result.output
    assert "username:  Testy" in result.output
    assert "gender:    male " in result.output


def test_get_snapshots(monkeypatch):
    user_id = '123'

    def mock_get(*args, **kwargs):
        return MockResponse(f'users/{user_id}/snapshots')

    runner = CliRunner()
    monkeypatch.setattr(requests, "get", mock_get)

    result = runner.invoke(get_snapshots, [user_id])
    assert "Snapshots taken by user 123:" in result.output
    assert "|        id | datetime      |" in result.output
    assert "| 123456789 | April 1, 2019 |" in result.output
    assert "| 123456889 | April 2, 2019 |" in result.output


def test_get_snapshot(monkeypatch):
    user_id = '123'
    snapshot_id = '123456789'

    def mock_get(*args, **kwargs):
        return MockResponse(f'users/{user_id}/snapshots/{snapshot_id}')

    runner = CliRunner()
    monkeypatch.setattr(requests, "get", mock_get)

    result = runner.invoke(get_snapshot, [user_id, snapshot_id])
    assert "Snapshot 123456789 taken by user 123:" in result.output
    assert "id:                 123456789" in result.output
    assert "datetime:           April 1, 2019" in result.output
    assert "available results:  pose, feelings" in result.output


def test_get_result(monkeypatch):
    user_id = '123'
    snapshot_id = '123456789'

    def mock_get(*args, **kwargs):
        return MockResponse(f'users/{user_id}/snapshots/{snapshot_id}/pose')

    runner = CliRunner()
    monkeypatch.setattr(requests, "get", mock_get)

    result = runner.invoke(get_result, [user_id, snapshot_id, 'pose'])
    assert "POSE of snapshot 123456789 taken by user 123:" in result.output
    assert "translation:  {'x': 0, 'y': 0, 'z': -1}" in result.output
    assert "rotation:     {'x': -0.5, 'y': 0.33, 'z': 0, 'w': 0.15}" \
           in result.output


def test_api_illegal_command():
    parser_proc = capture("python -m bci.api bad-command", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 2
    assert b'Usage: bci.api [OPTIONS] COMMAND [ARGS]' in err
    assert b'No such command "bad-command"' in err


def test_cli_illegal_command():
    parser_proc = capture("python -m bci.cli bad-command", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 2
    assert b'Usage: bci.cli [OPTIONS] COMMAND [ARGS]' in err
    assert b'No such command "bad-command"' in err


def test_api_help():
    parser_proc = capture("python -m bci.api", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 0
    assert b'Usage: bci.api [OPTIONS] COMMAND [ARGS]' in out
    assert b'run-server' in out


def test_cli_help():
    parser_proc = capture("python -m bci.cli", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 0
    assert b'Usage: bci.cli [OPTIONS] COMMAND [ARGS]' in out
    assert b'get-users' in out
    assert b'get-user\n' in out
    assert b'get-snapshots' in out
    assert b'get-snapshot\n' in out
    assert b'get-result' in out
