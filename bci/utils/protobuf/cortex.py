from protobuf3.message import Message
from protobuf3.fields import MessageField, EnumField, DoubleField, BytesField, UInt32Field, UInt64Field, FloatField, StringField
from enum import Enum


class User(Message):

    class Gender(Enum):
        MALE = 0
        FEMALE = 1
        OTHER = 2


class Snapshot(Message):
    pass


class Pose(Message):

    class Translation(Message):
        pass

    class Rotation(Message):
        pass


class ColorImage(Message):
    pass


class DepthImage(Message):
    pass


class Feelings(Message):
    pass

User.add_field('user_id', UInt64Field(field_number=1, optional=True))
User.add_field('username', StringField(field_number=2, optional=True))
User.add_field('birthday', UInt32Field(field_number=3, optional=True))
User.add_field('gender', EnumField(field_number=4, optional=True, enum_cls=User.Gender))
Snapshot.add_field('datetime', UInt64Field(field_number=1, optional=True))
Snapshot.add_field('pose', MessageField(field_number=2, optional=True, message_cls=Pose))
Snapshot.add_field('color_image', MessageField(field_number=3, optional=True, message_cls=ColorImage))
Snapshot.add_field('depth_image', MessageField(field_number=4, optional=True, message_cls=DepthImage))
Snapshot.add_field('feelings', MessageField(field_number=5, optional=True, message_cls=Feelings))
Pose.Translation.add_field('x', DoubleField(field_number=1, optional=True))
Pose.Translation.add_field('y', DoubleField(field_number=2, optional=True))
Pose.Translation.add_field('z', DoubleField(field_number=3, optional=True))
Pose.Rotation.add_field('x', DoubleField(field_number=1, optional=True))
Pose.Rotation.add_field('y', DoubleField(field_number=2, optional=True))
Pose.Rotation.add_field('z', DoubleField(field_number=3, optional=True))
Pose.Rotation.add_field('w', DoubleField(field_number=4, optional=True))
Pose.add_field('translation', MessageField(field_number=1, optional=True, message_cls=Pose.Translation))
Pose.add_field('rotation', MessageField(field_number=2, optional=True, message_cls=Pose.Rotation))
ColorImage.add_field('width', UInt32Field(field_number=1, optional=True))
ColorImage.add_field('height', UInt32Field(field_number=2, optional=True))
ColorImage.add_field('data', BytesField(field_number=3, optional=True))
DepthImage.add_field('width', UInt32Field(field_number=1, optional=True))
DepthImage.add_field('height', UInt32Field(field_number=2, optional=True))
DepthImage.add_field('data', BytesField(field_number=3, optional=True))
Feelings.add_field('hunger', FloatField(field_number=1, optional=True))
Feelings.add_field('thirst', FloatField(field_number=2, optional=True))
Feelings.add_field('exhaustion', FloatField(field_number=3, optional=True))
Feelings.add_field('happiness', FloatField(field_number=4, optional=True))
