import json
import uuid

from PIL import Image
from pathlib import Path

from ..parsers import BasicParser
from ..utils import DATA_DIR


class ColorImageParser(BasicParser):
    def parse(self, raw_snapshot_path):
        super().parse(raw_snapshot_path)

        # parse color image
        datapath = DATA_DIR / 'color_images'
        image_name = f'{uuid.uuid4().hex}.jpg'
        Path(datapath).mkdir(parents=True, exist_ok=True)

        color_pixels = []
        pixel = []
        for byte in self.snapshot.color_image.data:
            pixel.append(byte)
            if len(pixel) == 3:
                color_pixels.append(tuple(pixel))
                pixel = []
        image = Image.new('RGB', (self.snapshot.color_image.width,
                                  self.snapshot.color_image.height))
        image.putdata(color_pixels)
        image.save(datapath / image_name)

        # return metadata
        color_image = {
            'id': self.snapshot.datetime,  # snapshot ID is based on timestamp
            'height': self.snapshot.color_image.height,
            'width': self.snapshot.color_image.width,
            'image_url': f'/assets/color_images/{image_name}'
        }
        result = json.dumps(color_image)
        print(result)
        return result


parser_cls = ColorImageParser
