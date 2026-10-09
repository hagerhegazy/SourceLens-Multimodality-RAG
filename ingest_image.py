import os
from PIL import Image, ImageOps
from ingest_video import describe

def ingest_image(path):
    name = os.path.basename(path)
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")   # apply the rotation tag
    text = describe(img)
    return [{"id": f"{name}-img", "modality": "image", "content": text,
             "source": name, "location": 0, "thumb": os.path.abspath(path)}]