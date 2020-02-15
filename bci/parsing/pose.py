import json

from ..parsers import BasicParser

class PoseParser(BasicParser):
    def parse(self, raw_snapshot_path):
        super().parse(raw_snapshot_path)
        pose = {
            'translation': {
                'x': self.snapshot.pose.translation.x,
                'y': self.snapshot.pose.translation.y,
                'z': self.snapshot.pose.translation.z
            },
            'rotation': {
                'x': self.snapshot.pose.rotation.x,
                'y': self.snapshot.pose.rotation.y,
                'z': self.snapshot.pose.rotation.z,
                'w': self.snapshot.pose.rotation.w
            }
        }
        print(json.dumps(pose))

parser_cls = PoseParser
