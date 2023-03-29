from PIL.Image import Image
import io

from discord import File


def banner_file_handler(image: Image) -> File:
    with io.BytesIO() as image_binary:
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return File(fp=image_binary, filename='image.png')
