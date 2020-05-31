import json
import uuid

import numpy as np
from pathlib import Path
from matplotlib import pyplot as plt

from ..parsers import BasicParser
from ..utils import DATA_DIR


class DepthImageParser(BasicParser):
    def parse(self, raw_snapshot_path):
        super().parse(raw_snapshot_path)

        # parse depth image
        datapath = DATA_DIR / 'depth_images'
        image_name = f'{uuid.uuid4().hex}.png'
        Path(datapath).mkdir(parents=True, exist_ok=True)
        image = np.array(self.snapshot.depth_image.data).reshape(
            self.snapshot.depth_image.height, self.snapshot.depth_image.width
        )
        plt.imshow(image, cmap='hot', interpolation='nearest')
        plt.axis('off')
        plt.savefig(datapath / image_name,
                    bbox_inches='tight', pad_inches=0, dpi=48)

        # return metadata
        depth_image = {
            'id': self.snapshot.datetime,  # snapshot ID is based on timestamp
            'height': self.snapshot.depth_image.height,
            'width': self.snapshot.depth_image.width,
            'image_url': f'/assets/depth_images/{image_name}'
        }
        result = json.dumps(depth_image)
        print(result)
        return result


parser_cls = DepthImageParser
