import os
import time
import signal
import threading
from pathlib import Path

import pytest

from bci.server import run_server
from conftest import capture, WAIT_INTERVAL

log_path = Path(__file__).parents[1] / "log" / "server.log"

def test_run_server(prepare_good_protofile, capsys):
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5502 'rabbitmq://127.0.0.1:5672/'")
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "-p 5502 tests/good_proto.mind.gz")
    client_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert client_proc.returncode == 0
    assert 'Sent to users topic: {"user_id": 123, ' \
           '"username": "Test Testenson"' in log[-3]
    assert 'Sent to fanout: {"user_id": 123' in log[-2]
    assert 'Sent to snapshots topic: {"id":' in log[-1]

    server_proc.terminate()


def test_run_server_python_api(prepare_good_protofile):
    publisher = __import__(f'bci.publishers.rabbitmq', globals(), locals(),
                           'rabbitmq')
    server_proc = threading.Thread(target=run_server, args=(), kwargs={
        'host': '127.0.0.1', 'port': 5502, 'publish': publisher.publish,
        'publisher_host': '127.0.0.1', 'publisher_port': 5672
    }, daemon=True)
    server_proc.start()
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "-p 5502 tests/good_proto.mind.gz")
    client_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert client_proc.returncode == 0
    assert 'Sent to users topic: {"user_id": 123, ' \
           '"username": "Test Testenson"' in log[-3]
    assert 'Sent to fanout: {"user_id": 123' in log[-2]
    assert 'Sent to snapshots topic: {"id":' in log[-1]


def test_run_server_custom_publisher_func(prepare_good_protofile):
    def log_message(message, **kwargs):
        print(message, file=open('/tmp/test.log', 'a'))
    server_proc = threading.Thread(target=run_server, args=(), kwargs={
        'host': '127.0.0.1', 'port': 5501, 'publish': log_message
    }, daemon=True)
    server_proc.start()
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "-p 5501 tests/good_proto.mind.gz")
    client_proc.communicate()
    time.sleep(WAIT_INTERVAL)
    log = open('/tmp/test.log', 'r').read()
    assert client_proc.returncode == 0
    assert 'utils.protocol.UserData object' in log
    assert 'utils.protocol.Snapshot object' in log


def test_run_server_no_publisher_func(prepare_good_protofile, capsys):
    run_server()
    out, err = capsys.readouterr()
    assert 'ERROR: no publisher function provided' in err


def test_run_server_bad_port(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server -p 'bad_port' "
                          "tests/good_proto.mind.gz")
    out, err = server_proc.communicate()
    assert b'Usage: bci.server run-server' in err
    assert b'bad_port is not a valid integer' in err


def test_run_server_bad_hostname():
    server_proc = capture("python -m bci.server run-server -h 'bad_hostname' "
                          "'rabbitmq://127.0.0.1:5672/'")
    out, err = server_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert b'unknown host name "bad_hostname"' in err
    assert 'CRITICAL: unknown host name "bad_hostname"' in log[-1]


def test_run_server_unknown_publisher_module():
    server_proc = capture("python -m bci.server run-server "
                          "'unknown://127.0.0.1:5672/'")
    out, err = server_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert b'Publisher module "unknown" does not exist' in err
    assert 'CRITICAL: Publisher module "unknown" does not exist' in log[-1]


def test_run_server_no_publisher_host(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server "
                          "'rabbitmq://:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "tests/good_proto.mind.gz")
    time.sleep(WAIT_INTERVAL)
    log = open(log_path, 'r').readlines()
    assert 'CRITICAL: no host or port provided for publisher' in log[-1]
    server_proc.terminate()


def test_run_server_no_publisher_port(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server "
                          "'rabbitmq://127.0.0.1/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "tests/good_proto.mind.gz")
    time.sleep(WAIT_INTERVAL)
    log = open(log_path, 'r').readlines()
    assert 'CRITICAL: no host or port provided for publisher' in log[-1]
    server_proc.terminate()


def test_run_server_bad_publisher_host(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server "
                          "'rabbitmq://8.8.8.8:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "tests/good_proto.mind.gz")
    time.sleep(10)         # enough time for error to be logged
    log = open(log_path, 'r').readlines()
    assert 'CRITICAL: could not connect to rabbitmq through host 8.8.8.8 ' \
                'and port 5672' in log[-1]
    server_proc.terminate()


def test_run_server_bad_publisher_port(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server "
                          "'rabbitmq://127.0.0.1:60000/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "tests/good_proto.mind.gz", True)
    time.sleep(10)         # enough time for error to be logged
    log = open(log_path, 'r').readlines()
    assert 'CRITICAL: could not connect to rabbitmq through host 127.0.0.1 ' \
                'and port 60000' in log[-1]
    server_proc.terminate()



def test_run_server_missing_mq_url():
    server_proc = capture("python -m bci.server run-server", True)
    out, err = server_proc.communicate()

    assert server_proc.returncode == 2
    assert b'Usage: bci.server run-server' in err
    assert b'Missing argument "MESSAGE_QUEUE_URL"' in err


def test_server_illegal_command():
    server_proc = capture("python -m bci.server bad-command", True)
    out, err = server_proc.communicate()

    assert server_proc.returncode == 2
    assert b'Usage: bci.server [OPTIONS] COMMAND [ARGS]' in err
    assert b'No such command "bad-command"' in err


def test_server_help():
    server_proc = capture("python -m bci.server", True)
    out, err = server_proc.communicate()

    assert server_proc.returncode == 0
    assert b'Usage: bci.server [OPTIONS] COMMAND [ARGS]' in out
    assert b'run-server' in out
