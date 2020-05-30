import os
import time
import json
import signal
from pathlib import Path

import pytest
import requests
from click.testing import CliRunner

from bci.cli import (get_users, get_user, get_snapshots)
from conftest import capture, WAIT_INTERVAL


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

    result = runner.invoke(get_user, [user_id])
    assert "Snapshots taken by user 123:"
    assert "user_id:   123" in result.output
    assert "username:  Testy" in result.output
    assert "gender:    male " in result.output

# def test_save():
#     saver_proc = capture(f"python -m bci.saver save "
#                          f"-d 'mongodb://127.0.0.1:27017/' "
#                          f"'feelings' {tests_dir / 'sample_feelings.result'}")
#     out, err = saver_proc.communicate()
#     assert saver_proc.returncode == 0
#     client = pymongo.MongoClient('127.0.0.1:27017')
#     table = client.db['feelings']
#     results = list(table.find())
#     log = open(log_path, 'r').readlines()
#     assert results[0]['hunger'] == 0.5
#     assert results[0]['happiness'] == 0.7
#     assert "Saved to database table feelings" in log[-1]
#
#
#
# def test_save_python_api():
#     saver = Saver("mongodb://127.0.0.1:27017/")
#     data = json.dumps({'id': '123', 'attribute': 'value'})
#     saver.save('test_topic', data)
#     saver.save('test_topic', data)    # should ignore 2nd insertion
#     client = pymongo.MongoClient('127.0.0.1:27017')
#     table = client.db['test_topic']
#     results = list(table.find({}, {'id': 1, 'attribute': 1}))
#     assert len(results) == 1
#     assert results[0]['id'] == '123'
#     assert results[0]['attribute'] == 'value'
#
#
# def test_save_bad_data():
#     saver = Saver("mongodb://127.0.0.1:27017/")
#     with pytest.raises(Exception) as error:
#         saver.save('bad_topic', 'bad data')
#     assert "Illegal JSON data format" in str(error.value)
#     client = pymongo.MongoClient('127.0.0.1:27017')
#     table = client.db['bad_topic']
#     results = list(table.find({}, {'id': 1, 'attribute': 1}))
#     assert len(results) == 0
#
#
# def test_save_unsupported_db_service():
#     with pytest.raises(Exception) as error:
#         saver = Saver("nosql://127.0.0.1:27017/")
#     assert "Unsupported database service" in str(error.value)
#
#
# def test_save_bad_db_url():
#     saver = Saver("mongodb://8.8.8.8:27017/")
#     with pytest.raises(Exception) as error:
#         saver.save('test_topic', '{}')
#     assert "Could not connect to database on URL "
#     "8.8.8.8:27017" in str(error.value)


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
