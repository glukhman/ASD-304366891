from pathlib import Path

VERSION = 0.7
DEFAULT_FORMAT = 'protobuf'
DATA_DIR = Path(__file__).parent.parent.parent / 'data'

class MSG_TYPES:
    USER_DATA = 1
    SNAPSHOT = 2
