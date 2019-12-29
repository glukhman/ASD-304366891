import json
from pathlib import Path
from datetime import datetime


class Parser:
    def __init__(self, datapath, user_data):
        self.data_dir = Path(datapath)
        self.user_id = user_data.user_id
        self.path = None

    def parse(self, snapshot):
        timestamp = datetime.fromtimestamp(snapshot.timestamp/1000)
        timestamp = timestamp.strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.path = self.data_dir / str(self.user_id) / timestamp
        self.path.mkdir(parents=True, exist_ok=True)

class TranslationParser(Parser):
    def parse(self, snapshot):
        super().parse(snapshot)
        trans = {}
        trans['x'], trans['y'], trans['z'] = snapshot.translation
        with open(self.path / 'translation.json', 'w') as f:
             json.dump(trans, f)

class ColorImageParser(Parser):
    def parse(self, snapshot):
        super().parse(snapshot)
        snapshot.color_image.save(self.path / 'color_image.jpg')
