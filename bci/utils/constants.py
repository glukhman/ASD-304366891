from pathlib import Path

VERSION = 1.0
DEFAULT_FORMAT = 'protobuf'
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
SNAPSHOT_TOPICS = ['feelings', 'pose', 'color_image', 'depth_image']
TOPICS = SNAPSHOT_TOPICS + ['users', 'snapshots']


class MSG_TYPES:
    USER_DATA = 1
    SNAPSHOT = 2
