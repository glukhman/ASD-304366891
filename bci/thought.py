import struct
from datetime import datetime


class Thought:

    def __init__(self, user_id, timestamp, thought):
        self.user_id = user_id
        self.timestamp = timestamp
        self.thought = thought

    def __repr__(self):
        return f'Thought(user_id={self.user_id}, '\
               f'timestamp={self.timestamp.__repr__()}, '\
               f'thought="{self.thought}")'

    def __str__(self):
        timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f'[{timestamp}] user {self.user_id}: {self.thought}'

    def __eq__(self, other):
        if not isinstance(other, Thought):
            return False
        return (self.user_id == other.user_id) and \
               (self.timestamp == other.timestamp) and \
               (self.thought == other.thought)

    def serialize(self):
        message = self.thought.encode('utf-8')
        msg_size = len(message)
        msg_header = struct.pack('<qqI',
                                 self.user_id,
                                 int(self.timestamp.timestamp()),
                                 msg_size)
        return msg_header + message

    @classmethod
    def deserialize(cls, data):
        user_id, timestamp, msg_size = struct.unpack('<qqI', data[:20])
        timestamp = datetime.fromtimestamp(timestamp)
        thought = data[20:]
        if len(thought) != msg_size:
            raise Exception('data is incomplete')
        return Thought(user_id, timestamp, data[20:].decode('utf-8'))
