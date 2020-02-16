import gzip
import struct
import random
from datetime import datetime

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt, mpld3
from mpl_toolkits.mplot3d import Axes3D
import pytransform3d.rotations as pr

from ..utils.protobuf import cortex_pb2

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

    def read_snapshot(self, save_dir):
        idx = 0
        while True:
            try:
                #parse snapshot header
                msg_size, = struct.unpack('I', self.fp.read(4))
                snapshot = cortex_pb2.Snapshot()
                snapshot.ParseFromString(self.fp.read(msg_size))

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
                image.save(f'{save_dir}/color_image_{idx}.jpg')

                # parse depth image
                fig = plt.figure(figsize=(12,12), dpi=72)
                image = np.array(snapshot.depth_image.data).reshape(
                    snapshot.depth_image.height, snapshot.depth_image.width
                )
                plt.imshow(image, cmap='hot', interpolation='nearest')
                plt.axis('off')
                plt.savefig(f'{save_dir}/depth_image_{idx}.png',
                            bbox_inches='tight', pad_inches=0, dpi=48)

                # parse translation
                fig = plt.figure(figsize=(12,12), dpi=72)
                ax = fig.add_subplot(111, projection='3d')
                ax.set_xlim3d(-2,2)
                ax.set_ylim3d(-2,2)
                ax.set_zlim3d(-2,2)

                x = snapshot.pose.translation.x
                y = snapshot.pose.translation.y
                z = snapshot.pose.translation.z
                translation = [x, y, z]
                xline = np.linspace(x, 2, 100)
                yline = np.linspace(-2, y, 100)
                zline = np.linspace(-2, z, 100)

                ax.scatter(x, y, z, zdir='z', s=1000, c='b', depthshade=True)
                ax.plot(xline, [y]*100, [z]*100, c='b', alpha=0.7, ls='--')
                ax.plot([x]*100, yline, [z]*100, c='b', alpha=0.7, ls='--')
                ax.plot([x]*100, [y]*100, zline, c='b', alpha=0.7, ls='--')

                ax.view_init(elev = 20, azim = 120)
                plt.savefig(f'{save_dir}/translation_{idx}.png',
                            bbox_inches='tight', pad_inches=0, dpi=48)

                # parse rotation
                fig = plt.figure(figsize=(12,12), dpi=72)
                ax = fig.add_subplot(111, projection='3d')
                ax.set_xlim3d(-1,1)
                ax.set_ylim3d(-1,1)
                ax.set_zlim3d(-1,1)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_zticks([])

                a = np.linspace(.33*np.pi, 1.33*np.pi, 100)
                b = np.linspace(-.67*np.pi, .33*np.pi, 100)
                c = np.linspace(np.pi, 2*np.pi, 100)
                u = np.linspace(0, 2 * np.pi, 100)
                v = np.linspace(0, np.pi, 100)
                x = np.outer(np.cos(u), np.sin(v))
                y = np.outer(np.sin(u), np.sin(v))
                z = np.outer(np.ones(np.size(u)), np.cos(v))

                ax.plot_surface(x, y, z, color='cyan', lw=1, alpha=0.3)
                ax.plot(np.sin(a), np.cos(a), 0, c='b', alpha=0.3, ls='--')
                ax.plot(np.sin(b), np.cos(b), 0, c='b', alpha=0.7)
                ax.plot([0]*100, np.sin(v), np.cos(v), c='b', alpha=0.7)
                ax.plot([0]*100, np.sin(c), np.cos(c), c='b', alpha=0.3,
                        ls='--')

                rotation = [snapshot.pose.rotation.x, snapshot.pose.rotation.y,
                            snapshot.pose.rotation.z, snapshot.pose.rotation.w]
                vector = pr.q_prod_vector(np.array(rotation),
                                          np.array([0,0,1]))
                ax.quiver(0,0,0,*vector, length=1, linewidth=5,color='k')

                ax.view_init(elev = 20, azim = 120)
                plt.savefig(f'{save_dir}/rotation_{idx}.png',
                            bbox_inches='tight', pad_inches=0, dpi=48)

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
                      trans=tuple([f'{x:.2f}' for x in translation]),
                      rot=tuple([f'{x:.2f}' for x in rotation]),
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
        if format == 'protobuf':
            gender = reader.gender
        else:
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
