import json, os
import imageio_ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import config

def _remember(name, url, title):
    """Keep the original URL so the UI can later link to timestamps."""
    path = os.path.join("store", "sources.json")
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    data[name] = {"url": url, "title": title}
    os.makedirs("store", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def download_url(url, out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    opts = {
        "outtmpl": os.path.join(out_dir, "%(extractor)s_%(id)s.%(ext)s"),
        # one file with audio+video if available, otherwise separate streams that get merged
        "format": "b[height<=720]/bv*[height<=720]+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": os.getenv("YT_DEBUG") != "1",
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
    }
    browser = os.getenv("YT_COOKIES_BROWSER")          # only if a site needs login
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("_type") == "playlist":
                raise SystemExit("That link is a playlist. Paste the link of a single video.")
            if (info.get("duration") or 0) > config.MAX_VIDEO_SEC:
                raise SystemExit(f"Video is longer than {config.MAX_VIDEO_SEC}s, skipping.")
            info = ydl.extract_info(url, download=True)
            done = (info.get("requested_downloads") or [{}])[0].get("filepath")
            path = done or ydl.prepare_filename(info)
    except DownloadError as e:
        raise SystemExit(f"Download failed: {e}\nDownload the file by hand into data\\ "
                         "and ingest it by name instead.")
    if not os.path.exists(path):
        alt = os.path.splitext(path)[0] + ".mp4"
        path = alt if os.path.exists(alt) else path
    _remember(os.path.basename(path), url, info.get("title", ""))
    print("Downloaded", path)
    return path