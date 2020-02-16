import gzip
import struct
from datetime import datetime

from ..utils.protobuf import cortex_pb2


class ProtobufReader:
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.fp = gzip.open(self.filename, 'rb')
        # parse header
        msg_size, = struct.unpack('I', self.fp.read(4))
        user = cortex_pb2.User()
        user.ParseFromString(self.fp.read(msg_size))
        self.user_id, self.username, self.birthdate = \
            user.user_id, user.username, user.birthday
        if user.gender == user.MALE:
            self.gender = 'male'
        elif user.gender == user.FEMALE:
            self.gender = 'female'
        elif user.gender == user.OTHER:
            self.gender = 'other'

    def read_snapshot(self):
        while True:
            try:
                pack_data = bytes()

                #parse snapshot header
                msg_size, = struct.unpack('I', self.fp.read(4))
                snapshot = cortex_pb2.Snapshot()
                snapshot.ParseFromString(self.fp.read(msg_size))
                yield snapshot

            except struct.error:
                break

    def __exit__(self, exception, error, traceback):
        self.fp.close()


reader_cls = ProtobufReader
