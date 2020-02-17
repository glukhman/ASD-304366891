import os
import sys

import gzip
import pytest
import struct

from bci.utils.protobuf import cortex_pb2


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def prepare_good_protofile():
    raw_data = bytes()

    # serialize user data
    user_data = cortex_pb2.User()
    user_data.user_id = 123
    user_data.username = 'Test Testenson'
    user_data.birthday = 1000
    user_data.gender = user_data.OTHER
    raw_user_data = user_data.SerializeToString()
    raw_data += struct.pack('I', len(raw_user_data)) + raw_user_data

    # serialize snapshot
    snapshot = cortex_pb2.Snapshot()
    snapshot.datetime = 60000

    snapshot.pose.translation.x = 1
    snapshot.pose.translation.y = 2
    snapshot.pose.translation.z = 3
    snapshot.pose.rotation.x = -1
    snapshot.pose.rotation.y = -2
    snapshot.pose.rotation.z = -3
    snapshot.pose.rotation.w = -4

    snapshot.color_image.width = 1
    snapshot.color_image.height = 1
    snapshot.color_image.data = b'000'
    snapshot.depth_image.width = 0
    snapshot.depth_image.height = 0

    snapshot.feelings.hunger = .5
    snapshot.feelings.thirst = .3
    snapshot.feelings.exhaustion = .2
    snapshot.feelings.happiness = 1
    raw_snapshot = snapshot.SerializeToString()
    raw_data += struct.pack('I', len(raw_snapshot)) + raw_snapshot

    with gzip.GzipFile("tests/good_proto.mind.gz", "wb") as f:
        f.write(raw_data)


@pytest.fixture
def prepare_bad_protofile():
    with gzip.GzipFile("tests/bad_proto.mind.gz", "wb") as f:
        f.write(b'garbage data')


@pytest.fixture
def prepare_unzipped_protofile():
    with open("tests/unzipped_proto.mind.gz", "wb") as f:
        f.write(b'garbage data')
