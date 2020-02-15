import json

from .parsers import BasicParser

class PoseParser(BasicParser):
    def parse(self):
        super().parse()
        result = json.dumps(self.snapshot.pose)
        print(result)

parser_cls = PoseParser
