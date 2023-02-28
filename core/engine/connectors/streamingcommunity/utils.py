from typing import Optional

from PIL import ImageFile
from urllib.request import urlopen


def get_sizes(uri) -> Optional[tuple]:
    # get file size *and* image size (None if not known)
    file = urlopen(uri)
    p = ImageFile.Parser()
    while 1:
        data = file.read(1024)
        if not data:
            break
        p.feed(data)
        if p.image:
            return p.image.size
    file.close()
    return None


def get_ratio(uri):
    w, h = get_sizes(uri)
    return w/h
