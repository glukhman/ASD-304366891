import time
from pathlib import Path

from bci.client import upload_sample
from conftest import capture, WAIT_INTERVAL

log_path = Path(__file__).parents[1] / "log" / "client.log"


def test_upload_sample(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5500 'rabbitmq://127.0.0.1:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "-p 5500 tests/good_proto.mind.gz")

    client_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert client_proc.returncode == 0
    assert 'User data: OK!' in log[-2]
    assert 'Snapshot #1: OK!' in log[-1]
    server_proc.terminate()


def test_upload_sample_python_api(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5500 'rabbitmq://127.0.0.1:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    upload_sample(host='127.0.0.1', port=5500, path="tests/good_proto.mind.gz")

    log = open(log_path, 'r').readlines()
    assert 'User data: OK!' in log[-2]
    assert 'Snapshot #1: OK!' in log[-1]
    server_proc.terminate()


def test_upload_sample_default_host_port(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server "
                          "'rabbitmq://127.0.0.1:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/good_proto.mind.gz")

    client_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert client_proc.returncode == 0
    assert 'User data: OK!' in log[-2]
    assert 'Snapshot #1: OK!' in log[-1]
    server_proc.terminate()


def test_upload_sample_port_mismatch(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server -p 3955 "
                          "'rabbitmq://127.0.0.1:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -p 3966 "
                          "tests/good_proto.mind.gz")
    out, err = client_proc.communicate()
    assert b'Connection refused' in err
    server_proc.terminate()


def test_upload_sample_host_mismatch(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server -h '8.8.8.8' "
                          "'rabbitmq://127.0.0.1:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "tests/good_proto.mind.gz")
    out, err = client_proc.communicate()
    assert b'Connection refused' in err
    server_proc.terminate()


def test_upload_sample_bad_port(prepare_good_protofile):
    client_proc = capture("python -m bci.client upload-sample -p 'bad_port' "
                          "tests/good_proto.mind.gz")
    out, err = client_proc.communicate()
    assert b'Usage: bci.client upload-sample' in err
    assert b'bad_port is not a valid integer' in err


def test_upload_sample_damaged_data(prepare_bad_protofile):
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/bad_proto.mind.gz")
    out, err = client_proc.communicate()
    assert b'Error parsing message' in err


def test_upload_sample_bad_file_format(prepare_unzipped_protofile):
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/unzipped_proto.mind.gz")
    out, err = client_proc.communicate()
    assert b'Not a gzipped file' in err


def test_upload_sample_bad_filepath():
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/nosuch_file.gz")
    out, err = client_proc.communicate()
    assert b'No such file or directory' in err


def test_upload_sample_missing_filepath():
    client_proc = capture("python -m bci.client upload-sample")
    out, err = client_proc.communicate()

    assert client_proc.returncode == 2
    assert b'Usage: bci.client upload-sample' in err
    assert b'Missing argument "PATH"' in err


def test_upload_sample_unsupported_option():
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/good_proto.gz -x 1 ")
    out, err = client_proc.communicate()

    assert client_proc.returncode == 2
    assert b'Usage: bci.client upload-sample' in err
    assert b'no such option: -x' in err


def test_upload_sample_unsupported_args():
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/good_proto.gz extra-arg")
    out, err = client_proc.communicate()

    assert client_proc.returncode == 2
    assert b'Usage: bci.client upload-sample' in err
    assert b'Got unexpected extra argument' in err


def test_upload_sample_supported_file_format(prepare_good_protofile):
    server_proc = capture("python -m bci.server run-server "
                          "'rabbitmq://127.0.0.1:5672/'", True)
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/good_proto.mind.gz -f protobuf")
    out, err = client_proc.communicate()

    assert client_proc.returncode == 0
    assert b'User data: OK!' in out
    assert b'Snapshot #1: OK!' in out
    server_proc.terminate()


def test_upload_sample_unsupported_file_format():
    client_proc = capture("python -m bci.client upload-sample "
                          "tests/good_proto.mind.gz -f unknown")
    out, err = client_proc.communicate()
    assert b"module 'bci.readers' has no attribute 'unknown'" in err


def test_client_illegal_command():
    client_proc = capture("python -m bci.client bad-command")
    out, err = client_proc.communicate()

    assert client_proc.returncode == 2
    assert b'Usage: bci.client [OPTIONS] COMMAND [ARGS]' in err
    assert b'No such command "bad-command"' in err


def test_client_help():
    client_proc = capture("python -m bci.client")
    out, err = client_proc.communicate()

    assert client_proc.returncode == 0
    assert b'Usage: bci.client [OPTIONS] COMMAND [ARGS]' in out
    assert b'upload-sample' in out
