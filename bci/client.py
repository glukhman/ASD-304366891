from datetime import datetime
from .utils import Connection, DataReader, Hello, Config, Snapshot
from .thought import Thought


def upload_thought(address, user_id, thought):
    connection = Connection.connect(*address)
    with connection:
        thought = Thought(user_id, datetime.now(), thought)
        connection.send(thought.serialize())

# EX-6
def run(filepath, port):
    connection = Connection.connect('127.0.0.1', int(port))
    reader = DataReader(filepath)
    # generator for reading snapshots from data file
    snapshot_reader = reader.read_snapshot()

    with connection, reader:

        # send hello message to server
        hello_msg = Hello(reader.user_id, reader.username,
                          reader.birthdate, reader.gender)
        connection.send_message(hello_msg.serialize())

        # receive config message from server
        config_msg = connection.receive_message()
        config_msg = Config.deserialize(config_msg)

        # send snapshot to server
        reader.set_config_fields(config_msg.config_fields)
        snapshot_msg = Snapshot(snapshot_reader)
        connection.send_message(snapshot_msg.serialize())
