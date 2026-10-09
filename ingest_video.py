import os, cv2
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import config
from ocr import read_text
_proc = _model = None
def _blip():
    global _proc, _model
    if _model is None:
        _proc = BlipProcessor.from_pretrained(config.CAPTION_MODEL)
        _model = BlipForConditionalGeneration.from_pretrained(config.CAPTION_MODEL)
    return _proc, _model

def caption(img: Image.Image) -> str:
    proc, model = _blip()
    inputs = proc(images=img, return_tensors="pt")
    out = model.generate(**inputs, max_new_tokens=40)
    return proc.decode(out[0], skip_special_tokens=True)

def describe(img):
    text = caption(img)
    if config.USE_OCR:
        found = read_text(img)
        if found:
            text += f". Text on screen: {found}"
    return text

def _hist(frame):
    """Small color histogram, used to measure how different two frames look."""
    hsv = cv2.cvtColor(cv2.resize(frame, (64, 64)), cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
    return cv2.normalize(h, h).flatten()

def ingest_video(path):
    name = os.path.basename(path)
    out_dir = os.path.join(config.FRAMES_DIR, name)
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(1, int(fps * config.SAMPLE_EVERY_SEC))
    records, idx = [], 0
    last_text, last_hist, last_sec = None, None, -999.0
    while cap.grab():                      # grab() skips decoding, so it is fast
        if idx % step == 0:
            ok, frame = cap.retrieve()
            if ok:
                sec = idx / fps
                h = _hist(frame)
                changed = last_hist is None or cv2.compareHist(
                    last_hist, h, cv2.HISTCMP_BHATTACHARYYA) > config.SCENE_THRESHOLD
                gap = sec - last_sec
                if (changed and gap >= config.MIN_GAP_SEC) or gap >= config.MAX_GAP_SEC:
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    text = describe(img)
                    last_hist, last_sec = h, sec
                    if text != last_text:
                        thumb = os.path.join(out_dir, f"{int(sec)}.jpg")
                        img.save(thumb)
                        records.append({
                            "id": f"{name}-t{int(sec)}",
                            "modality": "frame",
                            "content": text,
                            "source": name,
                            "location": int(sec),
                            "thumb": thumb,
                        })
                    last_text = text
        idx += 1
    cap.release()
    return records