import json
from pathlib import Path

import pytest
import pymongo

from bci.saver import Saver
from conftest import capture

log_path = Path(__file__).parents[1] / "log" / "saver.log"
tests_dir = Path(__file__).parents[1] / "tests"


def test_save():
    saver_proc = capture(f"python -m bci.saver save "
                         f"-d 'mongodb://127.0.0.1:27017/' "
                         f"'feelings' {tests_dir / 'sample_feelings.result'}")
    out, err = saver_proc.communicate()
    assert saver_proc.returncode == 0
    client = pymongo.MongoClient('127.0.0.1:27017')
    table = client.db['feelings']
    results = list(table.find())
    log = open(log_path, 'r').readlines()
    assert results[0]['hunger'] == 0.5
    assert results[0]['happiness'] == 0.7
    assert "Saved to database table feelings" in log[-1]


def test_save_python_api():
    saver = Saver("mongodb://127.0.0.1:27017/")
    data = json.dumps({'id': '123', 'attribute': 'value'})
    saver.save('test_topic', data)
    saver.save('test_topic', data)    # should ignore 2nd insertion
    client = pymongo.MongoClient('127.0.0.1:27017')
    table = client.db['test_topic']
    results = list(table.find({}, {'id': 1, 'attribute': 1}))
    assert len(results) == 1
    assert results[0]['id'] == '123'
    assert results[0]['attribute'] == 'value'


def test_save_bad_data():
    saver = Saver("mongodb://127.0.0.1:27017/")
    with pytest.raises(Exception) as error:
        saver.save('bad_topic', 'bad data')
    assert "Illegal JSON data format" in str(error.value)
    client = pymongo.MongoClient('127.0.0.1:27017')
    table = client.db['bad_topic']
    results = list(table.find({}, {'id': 1, 'attribute': 1}))
    assert len(results) == 0


def test_save_unsupported_db_service():
    with pytest.raises(Exception) as error:
        Saver("nosql://127.0.0.1:27017/")
    assert "Unsupported database service" in str(error.value)


def test_save_bad_db_url():
    saver = Saver("mongodb://8.8.8.8:27017/")
    with pytest.raises(Exception) as error:
        saver.save('test_topic', '{}')
    assert "Could not connect to database on URL "
    "8.8.8.8:27017" in str(error.value)


def test_saver_illegal_command():
    parser_proc = capture("python -m bci.saver bad-command", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 2
    assert b'Usage: bci.saver [OPTIONS] COMMAND [ARGS]' in err
    assert b'No such command "bad-command"' in err


def test_saver_help():
    parser_proc = capture("python -m bci.saver", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 0
    assert b'Usage: bci.saver [OPTIONS] COMMAND [ARGS]' in out
    assert b'save' in out
    assert b'run-saver' in out
