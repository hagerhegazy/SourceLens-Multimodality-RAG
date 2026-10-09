from groq import Groq
import config
from retrieval import retrieve

LABELS = {
    "text": "pdf text",
    "frame": "video frame caption",
    "speech": "video speech transcript",
    "image": "image caption",
    "screen": "text shown on screen",
}

def cite(r):
    m = r["modality"]
    if m in ("frame", "speech", "screen"):
        s = int(r["location"])
        return f"[{r['source']} {s // 60:02d}:{s % 60:02d}]"
    if m == "image":
        return f"[{r['source']}]"
    return f"[{r['source']} p.{r['location']}]"

def answer(question, modality=None, sources=None):
    hits = retrieve(question, modality=modality, sources=sources)
    context = "\n".join(
        f"{cite(h)} ({LABELS[h['modality']]}): {h['content']}" for h in hits
    )
    prompt = (
        "You answer questions using the sources below. Sources are PDF text, "
        "captions of video frames or images, and transcripts of video speech. "
        "Captions are short, so combine them to describe what is shown. "
        "Cite each claim with its bracket tag, e.g. [report.pdf p.3] or "
        "[lecture.mp4 01:20]. Ignore sources that are unrelated to the question. "
        "Only reply 'Not found in the sources.' if none of the sources help.\n\n"
        f"SOURCES:\n{context}\n\nQUESTION: {question}"
    )
    client = Groq(api_key=config.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return resp.choices[0].message.content, hits