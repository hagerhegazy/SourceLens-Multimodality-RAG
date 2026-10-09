import json
import os
import shutil

import config
import store
from ingest_pdf import ingest_pdf
from ingest_video import ingest_video
from ingest_audio import ingest_speech
from ingest_image import ingest_image
from ingest_url import download_url
from merge import merge_frames_into_speech

VIDEO = (".mp4", ".mov", ".mkv", ".avi", ".webm")
IMAGE = (".jpg", ".jpeg", ".png", ".webp")


def ingest(arg):
    """Ingest a file path or a video link. Returns (file path, number of records)."""
    if arg.lower().startswith(("http://", "https://")):
        arg = download_url(arg)
    low = arg.lower()
    if low.endswith(".pdf"):
        recs = ingest_pdf(arg)
    elif low.endswith(VIDEO):
        recs = merge_frames_into_speech(ingest_video(arg), ingest_speech(arg))
    elif low.endswith(IMAGE):
        recs = ingest_image(arg)
    else:
        raise ValueError("Unsupported file type")
    store.delete_source(os.path.basename(arg))
    store.add_records(recs)
    return arg, len(recs)


def remove(name, delete_file=False):
    """Remove one source from the index, its saved frames and its link entry.
    The file in data/ is deleted only if delete_file is True."""
    store.delete_source(name)
    shutil.rmtree(os.path.join(config.FRAMES_DIR, name), ignore_errors=True)
    path = os.path.join("store", "sources.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.pop(name, None) is not None:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    if delete_file:
        file_path = os.path.join("data", name)
        if os.path.isfile(file_path):
            os.remove(file_path)
