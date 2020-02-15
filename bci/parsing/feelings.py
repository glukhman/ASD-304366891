import json

from ..parsers import BasicParser

class FeelingsParser(BasicParser):
    def parse(self, raw_snapshot_path):
        super().parse(raw_snapshot_path)
        feelings = {
            'hunger': self.snapshot.feelings.hunger,
            'thirst': self.snapshot.feelings.thirst,
            'exhaustion': self.snapshot.feelings.exhaustion,
            'happiness': self.snapshot.feelings.happiness
        }
        print(json.dumps(feelings))

parser_cls = FeelingsParser
