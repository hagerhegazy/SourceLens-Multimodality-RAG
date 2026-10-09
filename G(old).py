import json, os, re, shutil
from collections import Counter

import gradio as gr
import pymupdf
from PIL import Image

import store
from pipeline import ingest
from query import answer, cite

def load_sources():
    path = os.path.join("store", "sources.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def index_summary():
    data = store._col().get(include=["metadatas"])
    counts = Counter((m["source"], m["modality"]) for m in data["metadatas"])
    return "\n".join(f"{s}  [{m}]  x{n}" for (s, m), n in sorted(counts.items())) or "(empty)"

def source_names():
    data = store._col().get(include=["metadatas"])
    return sorted({m["source"] for m in data["metadatas"]})

def page_image(source, page_no):
    try:
        doc = pymupdf.open(os.path.join("data", source))
        pix = doc[page_no - 1].get_pixmap(dpi=70)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    except Exception:
        return None

def link_for(hit, sources):
    info = sources.get(hit["source"])
    if not info:
        return ""
    url = info["url"]
    if "youtube.com" in url or "youtu.be" in url:
        m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", url)
        if m and hit["modality"] in ("frame", "speech", "screen"):
            return f"https://www.youtube.com/watch?v={m.group(1)}&t={int(hit['location'])}s"
    return url

def evidence(hits):
    items = []
    for h in hits:
        img = None
        if h["modality"] == "text":
            img = page_image(h["source"], int(h["location"]))
        elif h.get("thumb") and os.path.exists(h["thumb"]):
            img = h["thumb"]
        if img is not None:
            items.append((img, f"{cite(h)}  score {h['score']:.1f}"))
    return items

def run_ingest(target):
    try:
        path, n = ingest(target)
        return f"Added {os.path.basename(path)} ({n} records)", os.path.basename(path)
    except (Exception, SystemExit) as e:
        return f"Failed: {target} ({e})", None

def add_sources(files, url):
    msgs, names = [], []
    for f in files or []:
        path = getattr(f, "name", f)
        dest = os.path.join("data", os.path.basename(path))
        if os.path.abspath(path) != os.path.abspath(dest):
            shutil.copy(path, dest)
        msg, name = run_ingest(dest)
        msgs.append(msg)
        if name:
            names.append(name)
    if url and url.strip():
        msg, name = run_ingest(url.strip())
        msgs.append(msg)
        if name:
            names.append(name)
    return ("\n".join(msgs) or "Nothing to add."), index_summary(), \
        gr.Dropdown(choices=source_names(), value=names)

def ask(question, scope):
    if not question or not question.strip():
        return "Type a question first.", [], ""
    try:
        text, hits = answer(question, sources=scope or None)
    except Exception as e:
        return f"Something went wrong: {e}", [], ""
    if "not found in the sources" in text.lower():
        return text, [], "No matching sources."
    sources = load_sources()
    lines = []
    for h in hits:
        tag = cite(h)
        link = link_for(h, sources)
        label = f"[{tag.strip('[]')}]({link})" if link else tag
        snippet = h["content"][:140].replace("\n", " ")
        lines.append(f"- {label} _(score {h['score']:.1f})_: {snippet}...")
    return text, evidence(hits), "\n".join(lines)

with gr.Blocks(title="Multimodal Knowledge Assistant") as demo:
    gr.Markdown("# Multimodal Knowledge Assistant\n"
                "1. Pick files or paste a video link, then click **Add to library** "
                "and wait for the status.\n"
                "2. Ask a question. Choose files in **Search only in** to limit the search "
                "(empty = all files).")
    with gr.Row():
        with gr.Column(scale=1):
            files = gr.File(label="Add files (PDF, video, image)", file_count="multiple")
            url = gr.Textbox(label="...or a video link", placeholder="https://...")
            add = gr.Button("Add to library")
            status = gr.Textbox(label="Status", interactive=False)
            library = gr.Textbox(label="In the library", value=index_summary,
                                 lines=14, interactive=False)
        with gr.Column(scale=2):
            scope = gr.Dropdown(choices=source_names(), value=[], multiselect=True,
                                label="Search only in (empty = all files)")
            question = gr.Textbox(label="Your question")
            go = gr.Button("Ask", variant="primary")
            ans = gr.Markdown()
            gallery = gr.Gallery(label="Evidence (source pages and frames)",
                                 columns=3, height=360)
            srcs = gr.Markdown()

    add.click(add_sources, [files, url], [status, library, scope])
    go.click(ask, [question, scope], [ans, gallery, srcs])
    question.submit(ask, [question, scope], [ans, gallery, srcs])

demo.launch()