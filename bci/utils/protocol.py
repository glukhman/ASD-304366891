import io
import struct
from datetime import datetime

from PIL import Image

class DataReader:
    def __init__(self, filename):
        self.filename = filename
        self.config_fields = []

    def __enter__(self):
        self.fp = open(self.filename, 'rb')
        # parse header
        self.user_id, username_length = struct.unpack('QI', self.fp.read(12))
        self.username = struct.unpack(
            f'{username_length}s', self.fp.read(username_length))[0].decode()
        self.birthdate, self.gender = struct.unpack('Ic', self.fp.read(5))

    def set_config_fields(self, config_fields):
        self.config_fields = config_fields

    def read_snapshot(self):
        while True:
            try:
                pack_data = bytes()

                # read snapshot header; do not parse!
                timestamp = self.fp.read(8)
                translation = self.fp.read(24)
                rotation = self.fp.read(32)
                if 'translation' not in self.config_fields:
                    translation = struct.pack('ddd', 0, 0, 0)
                if 'rotation' not in self.config_fields:
                    rotation = struct.pack('dddd', 0, 0, 0, 0)

                pack_data += timestamp + translation + rotation

                # read color image if requested; parse only dimensions
                color_dim = self.fp.read(8)
                if 'color_image' not in self.config_fields:
                    pack_data += struct.pack('II', 0, 0)
                else:
                    color_height, color_width = struct.unpack('II', color_dim)
                    pack_data += struct.pack('II', color_width, color_height)
                    pack_data += self.fp.read(3 * color_width * color_height)

                # read and depth image if requested; parse only dimensions
                depth_dim = self.fp.read(8)
                if 'depth_dim' not in self.config_fields:
                    pack_data += struct.pack('II', 0, 0)
                else:
                    depth_height, depth_width = struct.unpack('II', depth_dim)
                    pack_data += struct.pack('II', depth_width, depth_height)
                    pack_data += self.fp.read(4 * depth_width * depth_height)

                # read feelings; do not parse!
                feelings = self.fp.read(16)
                if 'feelings' not in self.config_fields:
                    feelings = struct.pack('ffff', 0, 0, 0, 0)
                pack_data += feelings

                yield pack_data

            except struct.error:
                break

    def __exit__(self, exception, error, traceback):
        self.fp.close()


class Hello:
    def __init__(self, user_id, username, birthdate, gender):
        self.user_id, self.username, self.birthdate, self.gender = \
            user_id, username, birthdate, gender

    def serialize(self):
        pack_username = self.username.encode()
        username_length = len(pack_username)
        pack_data = struct.pack('<QIIc',
                                 self.user_id,
                                 username_length,
                                 self.birthdate,
                                 self.gender)
        return pack_data + pack_username

    @classmethod
    def deserialize(cls, data):
        user_id, username_length, birthdate, gender = struct.unpack('<QIIc',
                                                                    data[:17])
        username = data[17:]
        if len(username) != username_length:
            raise Exception('data is incomplete')
        return Hello(user_id, username.decode(), birthdate, gender)


class Config:
    def __init__(self, config_fields):
        self.config_fields = config_fields

    def serialize(self):
        pack_data = struct.pack('<I', len(self.config_fields))
        for field in self.config_fields:
            pack_field = field.encode()
            pack_data += struct.pack('<I', len(pack_field)) + pack_field
        return pack_data

    @classmethod
    def deserialize(cls, data):
        offset = 4
        num_fileds, = struct.unpack('<I', data[:offset])
        fields = []
        for _ in range(num_fileds):
            field_length, = struct.unpack('<I', data[offset : offset+4])
            offset += 4
            field = data[offset : offset+field_length]
            offset += field_length
            fields.append(field.decode())
        return Config(fields)

class Snapshot:
    def __init__(self, snapshot_reader=None):
        self.snapshot_reader = snapshot_reader
        self.timestamp = None
        self.translation = None
        self.rotation = None
        self.color_image = None
        self.depth_image = None
        self.hunger, self.thirst, self.exhaustion, self.happiness = \
            None, None, None, None

    def serialize(self):
        return next(self.snapshot_reader)

    @classmethod
    def deserialize(cls, raw_data):
        ''' This happens on server-side'''
        bytereader = io.BytesIO(raw_data)

        # parse snapshot header
        timestamp, = struct.unpack('Q', bytereader.read(8))
        translation = struct.unpack('ddd', bytereader.read(24))
        rotation = struct.unpack('dddd', bytereader.read(32))
        color_width, color_height = struct.unpack('II', bytereader.read(8))

        # parse color image
        color_pixels = []
        for _ in range(color_height * color_width):
            B, G, R = struct.unpack('BBB', bytereader.read(3))
            color_pixels.append((R, G, B))  # fix byte order within pixel
        color_image = Image.new('RGB', (color_width, color_height))
        color_image.putdata(color_pixels)

        # parse depth image
        depth_height, depth_width = struct.unpack('II', bytereader.read(8))
        depth_pixels = []
        for _ in range(depth_height * depth_width):
            depth_pixels.append(struct.unpack('f', bytereader.read(4)),)
        depth_image = Image.new('L', (depth_width, depth_height))
        color_image.putdata(depth_pixels)

        # parse feelings
        hunger, thirst, exhaustion, happiness = \
            struct.unpack('ffff', bytereader.read(16))

        # create snapshot object
        snapshot = Snapshot()
        snapshot.timestamp = timestamp
        snapshot.translation = translation
        snapshot.rotation = rotation
        snapshot.color_image = color_image
        snapshot.depth_image = depth_image
        snapshot.hunger = hunger
        snapshot.thirst = thirst
        snapshot.exhaustion = exhaustion
        snapshot.happiness = happiness
        return snapshot
