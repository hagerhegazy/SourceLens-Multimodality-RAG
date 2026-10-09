import sys
import numpy as np
from PIL import Image, ImageOps
from ocr import _get

img = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert("RGB")
w, h = img.size
corners = {
    "bottom-left":  (0, int(h * 0.85), int(w * 0.30), h),
    "bottom-right": (int(w * 0.70), int(h * 0.85), w, h),
    "top-left":     (0, 0, int(w * 0.30), int(h * 0.15)),
    "top-right":    (int(w * 0.70), 0, w, int(h * 0.15)),
}
for name, box in corners.items():
    crop = img.crop(box)
    crop = crop.resize((crop.width * 4, crop.height * 4), Image.LANCZOS)
    res = _get().readtext(np.array(crop), min_size=5, low_text=0.3)
    print(name, [(t, round(float(c), 2)) for _, t, c in res])