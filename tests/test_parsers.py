import time
from pathlib import Path

from bci.parsers import run_parser
from conftest import capture, WAIT_INTERVAL

log_path = Path(__file__).parents[1] / "log" / "parsers.log"
tests_dir = Path(__file__).parents[1] / "tests"


def test_run_parser(prepare_good_protofile):
    parser_proc = capture("python -m bci.parsers run-parser 'feelings' "
                          "'rabbitmq://127.0.0.1:5672/'", True)
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5501 'rabbitmq://127.0.0.1:5672/'")
    time.sleep(WAIT_INTERVAL)
    client_proc = capture("python -m bci.client upload-sample -h '127.0.0.1' "
                          "-p 5501 tests/good_proto.mind.gz")
    client_proc.communicate()
    time.sleep(WAIT_INTERVAL)
    log = open(log_path, 'r').readlines()
    assert client_proc.returncode == 0
    assert 'Sent to feelings topic: {"id":' in log[-1]
    server_proc.terminate()
    parser_proc.terminate()


def test_run_parser_no_publisher_host(prepare_good_protofile):
    parser_proc = capture("python -m bci.parsers run-parser 'feelings' "
                          "'rabbitmq://:5672/'", True)
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5501 'rabbitmq://127.0.0.1:5672/'")
    time.sleep(WAIT_INTERVAL)
    capture("python -m bci.client upload-sample -h '127.0.0.1' "
            "-p 5501 tests/good_proto.mind.gz")
    time.sleep(20)
    log = open(log_path, 'r').readlines()
    assert 'no host or port provided for publisher service' in log[-1]
    server_proc.terminate()
    parser_proc.terminate()


def test_run_parser_bad_publisher_host(prepare_good_protofile):
    parser_proc = capture("python -m bci.parsers run-parser 'feelings' "
                          "'rabbitmq://8.8.8.8:5672/'", True)
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5501 'rabbitmq://127.0.0.1:5672/'")
    time.sleep(WAIT_INTERVAL)
    capture("python -m bci.client upload-sample -h '127.0.0.1' "
            "-p 5501 tests/good_proto.mind.gz")
    time.sleep(20)
    log = open(log_path, 'r').readlines()
    assert 'could not connect to rabbitmq through host 8.8.8.8 ' \
           'and port 5672' in log[-1]
    server_proc.terminate()
    parser_proc.terminate()


def test_run_parser_bad_publisher_port(prepare_good_protofile):
    parser_proc = capture("python -m bci.parsers run-parser 'feelings' "
                          "'rabbitmq://127.0.0.1:60000/'", True)
    server_proc = capture("python -m bci.server run-server -h '127.0.0.1' "
                          "-p 5501 'rabbitmq://127.0.0.1:5672/'")
    time.sleep(WAIT_INTERVAL)
    capture("python -m bci.client upload-sample -h '127.0.0.1' "
            "-p 5501 tests/good_proto.mind.gz")
    time.sleep(20)
    log = open(log_path, 'r').readlines()
    assert 'could not connect to rabbitmq through host 127.0.0.1 ' \
           'and port 60000' in log[-1]
    server_proc.terminate()
    parser_proc.terminate()


def test_run_parser_unknown_publisher_module():
    server_proc = capture("python -m bci.parsers run-parser 'feelings' "
                          "'unknown://127.0.0.1:5672/'")
    out, err = server_proc.communicate()
    log = open(log_path, 'r').readlines()
    assert b'Publisher module "unknown" does not exist' in err
    assert 'CRITICAL: Publisher module "unknown" does not exist' in log[-1]


def test_parse_pose(capsys):
    run_parser('pose', tests_dir / 'sample_snapshot.raw')
    out, err = capsys.readouterr()
    assert '"translation": {"x": -0.06974083930253983, "y": '
    '0.06346922367811203, "z": 0.9805684089660645}, "rotation": {"x": '
    '-0.25545328978610127, "y": -0.6929286539403685, "z": '
    '-0.23159210773864855, "w": 0.6332129127860687' in out


def test_parse_color_image(capsys):
    run_parser('color_image', tests_dir / 'sample_snapshot.raw')
    out, err = capsys.readouterr()
    assert '"height": 1080, "width": 1920, "image_url": "/assets/color_images'
    '/8294070f8e594596a0e559fe08e41d65.jpg"}' in out


def test_parse_unknown_parser_module(capsys):
    run_parser('unknown', tests_dir / 'sample_snapshot.raw')
    out, err = capsys.readouterr()
    assert "module 'bci.parsing' has no attribute 'unknown'" in err


def test_parse_bad_filepath(capsys):
    run_parser('feelings', tests_dir / 'nonsuch.file')
    out, err = capsys.readouterr()
    assert "No such file or directory" in err


def test_parse_bad_data(prepare_unzipped_protofile, capsys):
    run_parser('feelings', tests_dir / 'unzipped_proto.mind.gz')
    out, err = capsys.readouterr()
    assert "Error parsing message" in err


def test_parsers_illegal_command():
    parser_proc = capture("python -m bci.parsers bad-command", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 2
    assert b'Usage: bci.parsers [OPTIONS] COMMAND [ARGS]' in err
    assert b'No such command "bad-command"' in err


def test_parsers_help():
    parser_proc = capture("python -m bci.parsers", True)
    out, err = parser_proc.communicate()

    assert parser_proc.returncode == 0
    assert b'Usage: bci.parsers [OPTIONS] COMMAND [ARGS]' in out
    assert b'parse' in out
    assert b'run-parser' in out
