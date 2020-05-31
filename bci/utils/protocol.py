import io
import struct

from ..utils.constants import MSG_TYPES
from ..utils.protobuf import cortex_pb2


class UserData:
    def __init__(self, reader=None):
        self.user_id = reader.user_id if reader else None
        self.username = reader.username if reader else None
        self.birthdate = reader.birthdate if reader else None
        self.gender = reader.gender if reader else None

    def serialize(self):
        message = bytes()

        # Have any message begin with an unsigned 64-bit int containing the
        #  user's ID. this is done so the server won't have to manage a session
        #  with a specific user while receiving snapshots
        message += struct.pack('<IQ', MSG_TYPES.USER_DATA, self.user_id)
        packed = cortex_pb2.User()
        packed.user_id, packed.username, packed.birthday = \
            self.user_id, self.username, self.birthdate
        if self.gender == 'male':
            packed.gender = packed.MALE
        elif self.gender == 'female':
            packed.gender = packed.FEMALE
        elif self.gender == 'other':
            packed.gender = packed.OTHER

        packed = packed.SerializeToString()
        message += packed
        return message

    @classmethod
    def deserialize(cls, raw_data):
        ''' This happens on server-side'''
        bytereader = io.BytesIO(raw_data)

        user = cortex_pb2.User()
        user.ParseFromString(bytereader.read())
        user_data = UserData()
        user_data.user_id, user_data.username, user_data.birthdate = \
            user.user_id, user.username, user.birthday
        user_data.gender = user.gender
        return user_data


class Snapshot:
    def __init__(self, user_id=None, snapshot_data=None):
        self.user_id = user_id
        self.snapshot_data = snapshot_data
        self.datetime = None
        self.pose = None
        self.color_image = None
        self.depth_image = None
        self.feelings = None

    def serialize(self):
        message = bytes()

        # Have any message begin with an unsigned 64-bit int containing the
        #  user's ID. this is done so the server won't have to manage a session
        #  with a specific user while receiving snapshots
        message += struct.pack('<IQ', MSG_TYPES.SNAPSHOT, self.user_id)

        # Serialize the snapshot using protobuf3
        # Have an unsigned int with the packed snapshot size precede it
        snapshot = self.snapshot_data
        packed = cortex_pb2.Snapshot()
        packed.datetime = snapshot.datetime

        pose = packed.pose
        translation = pose.translation
        translation.x = snapshot.pose.translation.x
        translation.y = snapshot.pose.translation.y
        translation.z = snapshot.pose.translation.z
        rotation = pose.rotation
        rotation.x = snapshot.pose.rotation.x
        rotation.y = snapshot.pose.rotation.y
        rotation.z = snapshot.pose.rotation.z
        rotation.w = snapshot.pose.rotation.w

        color_image = packed.color_image
        color_image.width = snapshot.color_image.width
        color_image.height = snapshot.color_image.height
        color_image.data += snapshot.color_image.data

        depth_image = packed.depth_image
        depth_image.width = snapshot.depth_image.width
        depth_image.height = snapshot.depth_image.height
        depth_image.data.extend(snapshot.depth_image.data)

        feelings = packed.feelings
        feelings.hunger = snapshot.feelings.hunger
        feelings.thirst = snapshot.feelings.thirst
        feelings.exhaustion = snapshot.feelings.exhaustion
        feelings.happiness = snapshot.feelings.happiness

        packed = packed.SerializeToString()
        message += packed
        return message

    @classmethod
    def deserialize(cls, raw_data):
        ''' This happens on server-side'''
        bytereader = io.BytesIO(raw_data)

        parsed_snapshot = cortex_pb2.Snapshot()
        parsed_snapshot.ParseFromString(bytereader.read())
        snapshot = Snapshot()
        snapshot.datetime = parsed_snapshot.datetime
        snapshot.pose = parsed_snapshot.pose
        snapshot.color_image = parsed_snapshot.color_image
        snapshot.depth_image = parsed_snapshot.depth_image
        snapshot.feelings = parsed_snapshot.feelings
        return snapshot
