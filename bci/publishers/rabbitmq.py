import json
import logging
from datetime import datetime

import pika
from pathlib import Path

from ..utils import DATA_DIR, MSG_TYPES
from ..utils.protobuf import cortex_pb2


def publish(message, **kwargs):
    if (not kwargs['publisher_host']) or (not kwargs['publisher_port']):
        raise ConnectionError('no host or port provided for publisher service')

    # first check and establish connection
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            kwargs['publisher_host'], kwargs['publisher_port']))
    except pika.exceptions.AMQPConnectionError:
        error_msg = f"could not connect to rabbitmq through host " \
                    f"{kwargs['publisher_host']} and port " \
                    f"{kwargs['publisher_port']}"
        raise ConnectionError(error_msg)

    if kwargs['msg_type'] == MSG_TYPES.USER_DATA:
        # gender issues :)
        user_format = cortex_pb2.User()
        if message.gender == user_format.MALE:
            gender = 'male'
        elif message.gender == user_format.FEMALE:
            gender = 'female'
        elif message.gender == user_format.OTHER:
            gender = 'other'

        # format birthday
        birthdate = datetime.fromtimestamp(message.birthdate)
        birthdate = birthdate.strftime("%B %-d, %Y")

        # serialize user data
        user_data = {
            'user_id': message.user_id,
            'username': message.username,
            'birthday': birthdate,
            'gender': gender
        }
        user_data = json.dumps(user_data)

        channel = connection.channel()
        channel.exchange_declare(exchange='parse_results',
                                 exchange_type='topic')
        channel.basic_publish(exchange='parse_results',
                              routing_key='users', body=user_data)
        logging.info(f'Sent to users topic: {user_data}')
        connection.close()

    elif kwargs['msg_type'] == MSG_TYPES.SNAPSHOT:

        # save snapshot raw data to file system, using protobuf3
        timestamp = datetime.fromtimestamp(message.datetime/1000)
        timestamp = timestamp.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]

        datapath = DATA_DIR / str(kwargs['user_id']) / timestamp

        packed = cortex_pb2.Snapshot()
        packed.datetime = message.datetime
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
        data = {
            'user_id': kwargs['user_id'],
            'address': str(datapath / 'snapshot.raw')
        }
        data = json.dumps(data)

        channel = connection.channel()
        channel.exchange_declare(exchange='raw_snapshot',
                                 exchange_type='fanout')
        channel.basic_publish(exchange='raw_snapshot', routing_key='',
                              body=data)
        logging.info(f'Sent to fanout: {data}')
        connection.close()

        # serialize snapshot metadata
        timestamp = datetime.fromtimestamp(message.datetime/1000)
        timestamp = timestamp.strftime("%B %-d, %Y at %H:%M:%S.%f")[:-3]
        metadata = {
            'id': message.datetime,  # snapshot ID is based on timestamp
            'user_id': kwargs['user_id'],
            'datetime': timestamp
        }
        metadata = json.dumps(metadata)

        # publish the metadata of the snapshot to a topic exchange
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            kwargs['publisher_host'], kwargs['publisher_port']))
        channel = connection.channel()
        channel.exchange_declare(exchange='parse_results',
                                 exchange_type='topic')
        channel.basic_publish(exchange='parse_results',
                              routing_key='snapshots', body=metadata)
        logging.info(f'Sent to snapshots topic: {metadata}')
        connection.close()
