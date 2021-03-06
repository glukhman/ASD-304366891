import json

from ..parsers import BasicParser


class FeelingsParser(BasicParser):
    def parse(self, raw_snapshot_path):
        super().parse(raw_snapshot_path)
        feelings = {
            'id': self.snapshot.datetime,  # snapshot ID is based on timestamp
            'hunger': self.snapshot.feelings.hunger,
            'thirst': self.snapshot.feelings.thirst,
            'exhaustion': self.snapshot.feelings.exhaustion,
            'happiness': self.snapshot.feelings.happiness
        }
        result = json.dumps(feelings)
        print(result)
        return result


parser_cls = FeelingsParser
