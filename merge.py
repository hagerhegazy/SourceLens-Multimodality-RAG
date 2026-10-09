import re
import config

def merge_frames_into_speech(frames, speech):
    """Fold frame descriptions into the speech chunk covering the same time window.
    New on-screen text goes into its own short record (text already stored for this
    video is not repeated). Videos with almost no speech keep their frame records."""
    words = sum(len(s["content"].split()) for s in speech)
    if not config.MERGE_FRAMES or words < config.MIN_SPEECH_WORDS:
        return frames + speech
    speech = sorted(speech, key=lambda s: s["location"])
    seen = set()                       # on-screen words already stored for this video
    merged = []
    for i, s in enumerate(speech):
        start = 0 if i == 0 else s["location"]
        end = speech[i + 1]["location"] if i + 1 < len(speech) else float("inf")
        window = [f for f in frames if start <= f["location"] < end]
        captions, fresh_parts = [], []
        for f in window:
            cap, _, ocr = f["content"].partition(". Text on screen: ")
            captions.append(cap if config.SCREEN_RECORDS else f["content"])
            if ocr and config.SCREEN_RECORDS:
                tokens = re.findall(r"\w+", ocr)
                fresh = [t for t in tokens if t.lower() not in seen]
                seen.update(t.lower() for t in tokens)
                if len(fresh) >= 2:
                    fresh_parts.append(" ".join(fresh))
        captions = list(dict.fromkeys(captions))[:config.MAX_VISUALS]
        thumb = window[0]["thumb"] if window else s["thumb"]
        content = s["content"]
        if captions:
            content += " [Visual: " + "; ".join(captions) + "]"
        merged.append(dict(s, content=content, thumb=thumb))
        if fresh_parts:
            merged.append({"id": f"{s['id']}-screen", "modality": "screen",
                           "content": "Text shown on screen: " + "; ".join(dict.fromkeys(fresh_parts)),
                           "source": s["source"], "location": s["location"], "thumb": thumb})
    return merged