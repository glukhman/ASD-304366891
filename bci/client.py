import socket, struct
from datetime import datetime
from .utils import Connection
from .thought import Thought

def upload_thought(address, user_id, thought):
    connection = Connection.connect(*address)
    with connection:
        thought = Thought(user_id, datetime.now(), thought)
        connection.send(thought.serialize())
