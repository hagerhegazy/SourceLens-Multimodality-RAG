import numpy as np
from PIL import Image

import config

_reader = None


def _get():
    global _reader
    if _reader is None:
        import easyocr
        # OCR_LANGS in .env, e.g. "en,ar" to also read Arabic
        _reader = easyocr.Reader(config.OCR_LANGS, gpu=False, verbose=False)
    return _reader


# x0, y0, x1, y1 as fractions of the image: bottom-left, bottom-right, top-left, top-right
CORNERS = [(0.0, 0.85, 0.30, 1.0), (0.70, 0.85, 1.0, 1.0),
           (0.0, 0.0, 0.30, 0.15), (0.70, 0.0, 1.0, 0.15)]


def _read(arr, min_conf):
    results = _get().readtext(arr, min_size=5, low_text=0.3)
    return [t.strip() for _, t, c in results if c >= min_conf and len(t.strip()) >= 3]


def read_text(img, min_conf=0.3):
    """Text found in a PIL image, including small watermarks in the corners."""
    words = _read(np.array(img), min_conf)
    if config.OCR_CORNERS:
        w, h = img.size
        for x0, y0, x1, y1 in CORNERS:
            crop = img.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
            crop = crop.resize((crop.width * 4, crop.height * 4), Image.LANCZOS)
            words += _read(np.array(crop), min_conf)
    return " ".join(dict.fromkeys(words))
