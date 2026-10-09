import os, shutil, subprocess, tempfile
import imageio_ffmpeg
from groq import Groq
import config

WINDOW_SEC = 30                      # merge Whisper segments into ~30s chunks
MAX_BYTES = 24 * 1024 * 1024         # Groq upload limit is 25MB (free tier)

def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)

def _extract_audio(video_path, out_path):
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", video_path,
           "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", out_path]
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0

def _record(name, i, start, text):
    return {"id": f"{name}-s{i}", "modality": "speech", "content": text,
            "source": name, "location": int(start), "thumb": ""}

def ingest_speech(video_path):
    name = os.path.basename(video_path)
    tmp = tempfile.mkdtemp()
    audio = os.path.join(tmp, "audio.mp3")
    try:
        if not _extract_audio(video_path, audio):
            print("No audio track found, skipping speech.")
            return []
        if os.path.getsize(audio) > MAX_BYTES:
            print("Audio is over Groq's 25MB limit, skipping speech.")
            return []
        with open(audio, "rb") as f:
            resp = Groq(api_key=config.GROQ_API_KEY).audio.transcriptions.create(
                file=("audio.mp3", f.read()),
                model=config.WHISPER_MODEL,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    records, buf, start = [], [], 0.0
    for seg in _get(resp, "segments") or []:
        if not buf:
            start = _get(seg, "start")
        buf.append(_get(seg, "text").strip())
        if _get(seg, "end") - start >= WINDOW_SEC:
            records.append(_record(name, len(records), start, " ".join(buf)))
            buf = []
    if buf:
        records.append(_record(name, len(records), start, " ".join(buf)))
    return records