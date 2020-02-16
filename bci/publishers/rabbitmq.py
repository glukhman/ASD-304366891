import os
from datetime import datetime

import pika
from pathlib import Path

from ..utils import DATA_DIR, MSG_TYPES
from ..utils.protobuf import cortex_pb2


def publish(message, msg_type, user_id, **kwargs):
    if (not kwargs['publisher_host']) or (not kwargs['publisher_port']):
        raise Exception('no host or port provided for publisher service')

    if msg_type == MSG_TYPES.SNAPSHOT:

        # save snapshot raw data to file system, using protobuf3
        timestamp = datetime.fromtimestamp(message.datetime/1000)
        timestamp = timestamp.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
        print(timestamp)

        datapath = DATA_DIR / str(user_id) / timestamp

        packed = cortex_pb2.Snapshot()
        pose = packed.pose
        translation = pose.translation
        translation.x = message.pose.translation.x
        translation.y = message.pose.translation.y
        translation.z = message.pose.translation.z
        rotation = pose.rotation
        rotation.x = message.pose.rotation.x
        rotation.y = message.pose.rotation.y
        rotation.z = message.pose.rotation.z
        rotation.w = message.pose.rotation.w

        color_image = packed.color_image
        color_image.width = message.color_image.width
        color_image.height = message.color_image.height
        color_image.data += message.color_image.data

        depth_image = packed.depth_image
        depth_image.width = message.depth_image.width
        depth_image.height = message.depth_image.height
        depth_image.data.extend(message.depth_image.data)

        feelings = packed.feelings
        feelings.hunger = message.feelings.hunger
        feelings.thirst = message.feelings.thirst
        feelings.exhaustion = message.feelings.exhaustion
        feelings.happiness = message.feelings.happiness

        packed = packed.SerializeToString()

        Path(datapath).mkdir(parents=True, exist_ok=True)
        with open(datapath / 'snapshot.raw', 'wb') as f:
            f.write(packed)

        # publish the address of the raw snapshot to a fanout exchange

        connection = pika.BlockingConnection(pika.ConnectionParameters(
            kwargs['publisher_host'], kwargs['publisher_port']))
        channel = connection.channel()

        channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')
        message = str(datapath / 'snapshot.raw')
        channel.basic_publish(exchange='raw_snapshot', routing_key='',
                              body=message)
        print(" [x] Sent %r" % message)
        connection.close()
