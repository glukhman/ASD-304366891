import gzip
import struct
from datetime import datetime

from PIL import Image

from ..utils.protobuf import cortex

class BinaryReader:
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.fp = open(self.filename, 'rb')
        # parse header
        self.user_id, username_length = struct.unpack('QI', self.fp.read(12))
        self.username = struct.unpack(
            f'{username_length}s', self.fp.read(username_length))[0].decode()
        self.birthdate, self.gender = struct.unpack('Ic', self.fp.read(5))

    def read_snapshot(self, save_dir):
        idx = 0
        while True:
            try:
                #parse snapshot header
                timestamp, = struct.unpack('Q', self.fp.read(8))
                translation = struct.unpack('ddd', self.fp.read(24))
                rotation = struct.unpack('dddd', self.fp.read(32))
                color_height, color_width = struct.unpack('II', self.fp.read(8))
                # parse color image
                color_pixels = []
                for _ in range(color_height):
                    for _ in range(color_width):
                        B, G, R = struct.unpack('BBB', self.fp.read(3))
                        color_pixels.append((R, G, B))  # fix byte order within pixel
                image = Image.new('RGB', (color_width, color_height))
                image.putdata(color_pixels)
                image.save(f'{save_dir}/color_image_{idx}.jpg')
                # parse depth image
                depth_height, depth_width = struct.unpack('II', self.fp.read(8))
                depth_pixels = []
                for _ in range(depth_height):
                    for _ in range(depth_width):
                        depth_pixels.append(struct.unpack('f', self.fp.read(4)), )
                # parse feelings
                hunger, thirst, exhaustion, happiness = \
                    struct.unpack('ffff', self.fp.read(16))
                # print result
                timestamp = datetime.fromtimestamp(timestamp/1000)
                print('\nSnapshot from {time} on {trans} / {rot} with a '
                      '{color_dim} color image and a {depth_dim} depth image.'
                      f'\nfeelings={hunger}, {thirst}, {exhaustion}, {happiness}'
                      .format(
                      time=timestamp.strftime("%B %-d, %Y at %H:%M:%S.%f")[:-3],
                      trans=tuple(f'{x:.2f}' for x in translation),
                      rot=tuple(f'{x:.2f}' for x in rotation),
                      color_dim=f'{color_height}x{color_width}',
                      depth_dim=f'{depth_height}x{depth_width}',
                ))
                idx += 1
                yield
            except struct.error:
                break

    def __exit__(self, exception, error, traceback):
        self.fp.close()


class ProtobufReader:
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.fp = gzip.open(self.filename, 'rb')
        # parse header
        msg_size, = struct.unpack('I', self.fp.read(4))
        user = cortex.User()
        user.parse_from_bytes(self.fp.read(msg_size))
        self.user_id, self.username, self.birthdate, self.gender = \
            user.user_id, user.username, user.birthday, user.gender

    def read_snapshot(self, save_dir):
        idx = 0
        while True:
            try:
                #parse snapshot header
                msg_size, = struct.unpack('I', self.fp.read(4))
                snapshot = cortex.Snapshot()
                snapshot.parse_from_bytes(self.fp.read(msg_size))

                # parse color image
                color_pixels = []
                pixel = []
                for byte in snapshot.color_image.data:
                    pixel.append(byte)
                    if len(pixel)==3:
                        color_pixels.append(tuple(pixel))
                        pixel = []
                image = Image.new('RGB', (snapshot.color_image.width,
                                          snapshot.color_image.height))
                image.putdata(color_pixels)
                image.save(f'{save_dir}/color_image_{idx}.pbuf.jpg')

                # parse depth image
                depth_pixels = []
                for byte in snapshot.depth_image.data:
                    pixel.append(byte)
                    if len(pixel)==4:
                        pixel = bytearray(pixel)
                        depth_pixels.append(struct.unpack('f', pixel))
                        pixel = []
                print(depth_pixels)
                # TODO: print to screen using matplotlib



                # print result
                timestamp = datetime.fromtimestamp(snapshot.datetime/1000)
                print('\nSnapshot from {time} on {trans} / {rot} with a '
                      '{color_dim} color image and a {depth_dim} depth image.'
                      f'\nfeelings={snapshot.feelings.hunger}, '
                      f'{snapshot.feelings.thirst}, '
                      f'{snapshot.feelings.exhaustion}, '
                      f'{snapshot.feelings.happiness}'
                      .format(
                      time=timestamp.strftime("%B %-d, %Y at %H:%M:%S.%f")[:-3],
                      trans=(f'{snapshot.pose.translation.x:.2f}',
                             f'{snapshot.pose.translation.y:.2f}',
                             f'{snapshot.pose.translation.z:.2f}'),
                      rot=(f'{snapshot.pose.rotation.x:.2f}',
                           f'{snapshot.pose.rotation.y:.2f}',
                           f'{snapshot.pose.rotation.z:.2f}',
                           f'{snapshot.pose.rotation.w:.2f}'),
                      color_dim=f'{snapshot.color_image.height}x'
                                f'{snapshot.color_image.width}',
                      depth_dim=f'{snapshot.depth_image.height}x'
                                f'{snapshot.depth_image.width}',
                ))
                idx += 1
                yield
            except struct.error:
                break

    def __exit__(self, exception, error, traceback):
        self.fp.close()


def read(filename, format):
    if format == 'protobuf':
        reader = ProtobufReader(filename)
    else:
        reader = BinaryReader(filename)
    with reader:
        birthdate = datetime.fromtimestamp(reader.birthdate)
        gender = 'male' if reader.gender == b'm' else 'female'
        print(f'user {reader.user_id}: {reader.username}, '
              f'born {birthdate.strftime("%B %-d, %Y")} ({gender})')

        snapshot_reader = reader.read_snapshot('data')
        next(snapshot_reader)
        next(snapshot_reader)
        next(snapshot_reader)

        # THIS ALSO WORKS:
        # while True:
        #     try:
        #         next(snapshot_reader)
        #     except StopIteration:
        #         break
