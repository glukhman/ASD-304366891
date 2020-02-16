import json

from ..parsers import BasicParser


class PoseParser(BasicParser):
    def parse(self, raw_snapshot_path):
        super().parse(raw_snapshot_path)
        pose = {
            'id': self.snapshot.datetime, # snapshot ID is based on timestamp
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
        result = json.dumps(pose)
        print(result)
        return result

parser_cls = PoseParser
