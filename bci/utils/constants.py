from pathlib import Path

VERSION = 0.7
DEFAULT_FORMAT = 'protobuf'
DATA_DIR = Path(__file__).parent.parent.parent / 'data'

class MSG_TYPES:
    USER_DATA = 1
    SNAPSHOT = 2

SNAPSHOT_TOPICS = ['feelings', 'pose', 'color_image', 'depth_image']
TOPICS = SNAPSHOT_TOPICS + ['users', 'snapshots']
