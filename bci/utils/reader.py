import struct
from datetime import datetime

from PIL import Image

class Reader:
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
                      .format(
                      time=timestamp.strftime("%B %-d, %Y at %H:%M:%S.%f")[:-3],
                      trans=tuple(f'{x:.2f}' for x in translation),
                      rot=tuple(f'{x:.2f}' for x in rotation),
                      color_dim=f'{color_height}x{color_width}',
                      depth_dim=f'{depth_height}x{depth_width}',
                ))
                idx += 1    #not sure if necessary
                yield
            except struct.error:
                break

    def __exit__(self, exception, error, traceback):
        self.fp.close()



def read(filename):
    reader = Reader(filename)
    with reader:
        birthdate = datetime.fromtimestamp(reader.birthdate)
        gender = 'male' if reader.gender == b'm' else 'female'
        print(f'user {reader.user_id}: {reader.username}, '
              f'born {birthdate.strftime("%B %-d, %Y")} ({gender})')

        snapshot_reader = reader.read_snapshot('data')
        next(snapshot_reader)

        # THIS ALSO WORKS:
        # while True:
        #     try:
        #         next(snapshot_reader)
        #     except StopIteration:
        #         break
