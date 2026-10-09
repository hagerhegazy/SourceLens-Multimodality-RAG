"""SourceLens web UI (Gradio) with a custom dark-blue and light-yellow theme."""
import html
import inspect
import json
import os
import re
import shutil
from collections import Counter

import gradio as gr
import pymupdf
from PIL import Image

import store
from pipeline import ingest, remove
from query import answer, cite

# ---------------------------------------------------------------- look and feel
VARS = dict(
    body_background_fill="#070d24", background_fill_primary="#0d1636",
    background_fill_secondary="#101a3d", block_background_fill="#0d1636",
    block_border_color="#ffe9a024", block_label_background_fill="#142046",
    block_label_text_color="#ffe9a0", block_title_text_color="#ffe9a0",
    body_text_color="#e9edff", body_text_color_subdued="#8f9bc4",
    border_color_primary="#ffe9a02e", input_background_fill="#0a1230",
    input_border_color="#ffe9a02e", button_primary_background_fill="#f5c542",
    button_primary_background_fill_hover="#ffe9a0", button_primary_text_color="#0a1030",
    button_secondary_background_fill="transparent", button_secondary_text_color="#ffe9a0",
)
THEME = gr.themes.Base(
    primary_hue="yellow", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
).set(**VARS, **{k + "_dark": v for k, v in VARS.items()})

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&display=swap');
:root{--navy:#070d24;--panel:#0d1636;--panel2:#142046;--gold:#ffe9a0;--gold2:#f5c542;--mute:#8f9bc4}
.gradio-container{width:calc(100% - 80px)!important;max-width:1600px!important;margin-left:auto!important;margin-right:auto!important;background:radial-gradient(1100px 560px at 8% -10%,#1b2a6b66,transparent),radial-gradient(900px 480px at 100% 0%,#f5c54226,transparent),var(--navy)!important}
footer{display:none!important}
.hero{display:flex;align-items:center;justify-content:center;text-align:center;gap:16px;padding:26px 8px 6px}.hero>div{text-align:center}
.hero svg{width:56px;height:56px;filter:drop-shadow(0 0 14px #ffe9a080)}
.hero h1{margin:0;font:700 42px/1.1 'Playfair Display',Georgia,serif;background:linear-gradient(90deg,#fff3c4,#f5c542,#fff3c4);background-size:200% auto;-webkit-background-clip:text;background-clip:text;color:transparent;animation:shine 6s linear infinite}
.hero p{margin:4px 0 0;color:var(--mute);font-size:15px}
@keyframes shine{to{background-position:200% center}}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0 6px}
.stats div{flex:1;min-width:150px;background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid #ffe9a026;border-radius:16px;padding:12px 16px;box-shadow:0 8px 30px #00000055}
.stats b{display:block;font:700 26px 'Playfair Display',Georgia,serif;color:var(--gold)}
.stats span{color:var(--mute);font-size:12px;letter-spacing:.08em;text-transform:uppercase}
.block{border:1px solid #ffe9a022!important;border-radius:18px!important;box-shadow:0 10px 40px #00000066;transition:border-color .25s,box-shadow .25s}
.block:hover{border-color:#ffe9a05c!important;box-shadow:0 12px 44px #f5c54218,0 10px 40px #00000066}
button.primary{background:linear-gradient(135deg,#fff0b3,#f5c542)!important;color:#0a1030!important;font-weight:700!important;border:0!important;border-radius:12px!important;box-shadow:0 6px 22px #f5c54255;transition:transform .15s,box-shadow .15s}
button.primary:hover{transform:translateY(-2px);box-shadow:0 10px 30px #f5c54288}
button.secondary{background:transparent!important;border:1px solid #ffe9a066!important;color:var(--gold)!important;border-radius:12px!important}
button.secondary:hover{background:#ffe9a014!important}
textarea,input{border-radius:12px!important}
input,textarea{background:#0a1230!important;color:#8f9bc4!important}
input::placeholder,textarea::placeholder{color:#8f9bc4!important;opacity:1!important}
/* Uploaded-file preview: force dark blue styling */
.file-preview,
.file-preview *,
.file-preview > *,
[data-testid="file"],
[data-testid="file"] *,
.file-upload,
.file-upload *,
.upload-container,
.upload-container *,
button.file-preview,
.file-preview button {
background-color: #0a1230 !important;
color: #e9edff !important;
border-color: #ffe9a02e !important;
}

.file-preview svg,
[data-testid="file"] svg {
color: #ffe9a0 !important;
fill: none !important;
}

input[type="file"],
input[type="file"]::file-selector-button {
background-color: #0a1230 !important;
color: #e9edff !important;
}

.pill{display:flex;justify-content:space-between;gap:10px;padding:9px 12px;margin:6px 0;border-radius:12px;background:#ffe9a00d;border:1px solid #ffe9a022;font-size:13px;color:#e9edff}
.pill em{color:var(--mute);font-style:normal;text-align:right}
.empty{color:var(--mute);padding:10px}
.answer{white-space:pre-wrap;font:19px/1.65 'Playfair Display',Georgia,serif;color:#fff8dc;padding:18px 20px;border-left:3px solid var(--gold2);background:linear-gradient(90deg,#ffe9a012,transparent);border-radius:0 14px 14px 0}
.cite{display:inline-block;background:var(--gold);color:#0a1030;border-radius:7px;padding:0 7px;margin:0 2px;font:600 12px ui-monospace,Consolas,monospace}
.src{padding:10px 2px;border-top:1px solid #ffe9a01c;font-size:13px;color:#e9edff}
.src a,.src b{color:var(--gold)}
.src em{color:var(--mute);margin-left:8px;font-style:normal}
.src p{margin:4px 0 0;color:var(--mute)}
.hint{color:var(--gold2);font-size:13px;margin-top:10px}
.grid-wrap img,.gallery-item img{transition:transform .25s}
.gallery-item:hover img{transform:scale(1.04)}
.flat,.flat:hover{border:0!important;box-shadow:none!important;background:transparent!important;padding:0!important;min-height:0!important}
button.primary:active {
    transform: scale(0.97) !important;
    box-shadow: 0 0 12px #f5c542aa !important;
}

button:disabled {
    cursor: wait !important;
    opacity: 0.65 !important;
}
.recent-questions {
    margin-top: 40px !important;
}
"""

HERO = """<div class="hero"><svg viewBox="0 0 64 64" fill="none"><circle cx="27" cy="27" r="17" stroke="#ffe9a0" stroke-width="4"/><path d="M40 40l16 16" stroke="#f5c542" stroke-width="5" stroke-linecap="round"/><path d="M27 17v20M17 27h20" stroke="#ffe9a0" stroke-width="2.5" stroke-linecap="round" opacity=".7"/></svg><div><h1>SourceLens</h1><p>Ask your PDFs, videos and images. Every answer shows its evidence.</p></div></div>"""
JS = """() => {
  const SEL = '#scope-dd';
  // Clicking the arrow or any empty part of the box opens or closes the list.
  document.addEventListener('mousedown', e => {
    const root = e.target.closest(SEL);
    if (!root) return;
    if (e.target.closest('[role="option"], [role="button"], button, .token-remove, .remove-all')) return;
    const input = root.querySelector('input');
    if (!input || e.target === input) return;
    e.preventDefault();
    if (document.activeElement === input) input.blur(); else input.focus();
  }, true);
  // After choosing a file in the list, close it.
  document.addEventListener('click', e => {
    if (e.target.closest(SEL + ' [role="option"]')) {
      setTimeout(() => { const a = document.activeElement; if (a && a.closest(SEL)) a.blur(); }, 60);
    }
  });
}"""

# ---------------------------------------------------------------- helpers
def _metas():
    return store._col().get(include=["metadatas"])["metadatas"]


def source_names():
    return sorted({m["source"] for m in _metas()})


def stats_html():
    metas = _metas()
    return ('<div class="stats">'
            f'<div><b>{len({m["source"] for m in metas})}</b><span>sources</span></div>'
            f'<div><b>{len(metas)}</b><span>searchable passages</span></div>'
            '<div><b>Hybrid + rerank</b><span>search engine</span></div></div>')


def library_html():
    by = {}
    for (src, kind), n in Counter((m["source"], m["modality"]) for m in _metas()).items():
        by.setdefault(src, []).append(f"{n} {kind}")
    if not by:
        return '<div class="empty">Your library is empty. Add a file to begin.</div>'
    return "".join(f'<div class="pill"><span>{html.escape(s)}</span><em>{html.escape(", ".join(v))}</em></div>'
                   for s, v in sorted(by.items()))


def refresh(selected=None):
    names = source_names()
    return (stats_html(), library_html(),
            gr.Dropdown(choices=names, value=selected or []),
            gr.Dropdown(choices=names, value=None))


def load_sources():
    path = os.path.join("store", "sources.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


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
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", url)
    if m and "youtu" in url and hit["modality"] in ("frame", "speech", "screen"):
        return f"https://www.youtube.com/watch?v={m.group(1)}&t={int(hit['location'])}s"
    return url


def evidence(hits):
    items = []
    for h in hits:
        img = page_image(h["source"], int(h["location"])) if h["modality"] == "text" else (
            h["thumb"] if h.get("thumb") and os.path.exists(h["thumb"]) else None)
        if img is not None:
            items.append((img, f"{cite(h)}  score {h['score']:.1f}"))
    return items

def show(items):
    return gr.update(value=items, visible=bool(items))

def render_answer(text):
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\[([^\[\]]+)\]", r'<span class="cite">\1</span>', safe)
    return f'<div class="answer">{safe}</div>'


def note(msg):
    return f'<div class="answer">{html.escape(msg)}</div>'


def ocr_hint(scope):
    """Explain a 'Not found' on an image whose OCR found no text."""
    bare = []
    for name in scope or []:
        rec = store._col().get(where={"source": name}, include=["documents", "metadatas"])
        for doc, meta in zip(rec["documents"], rec["metadatas"]):
            if meta["modality"] == "image" and "Text on screen:" not in doc:
                bare.append(name)
    if not bare:
        return ""
    return ('<div class="hint">OCR found no readable text in ' + html.escape(", ".join(bare))
            + '. Small, handwritten or Arabic text may need OCR_LANGS=en,ar in your .env.</div>')


# ---------------------------------------------------------------- actions
def _run_ingest(target):
    try:
        path, n = ingest(target)
        return f"Added {os.path.basename(path)} ({n} passages)", os.path.basename(path)
    except (Exception, SystemExit) as e:
        return f"Failed: {target} ({e})", None


def add_sources(files, url):
    msgs, names = [], []
    for f in files or []:
        path = getattr(f, "name", f)
        dest = os.path.join("data", os.path.basename(path))
        if os.path.abspath(path) != os.path.abspath(dest):
            shutil.copy(path, dest)
        msg, name = _run_ingest(dest)
        msgs.append(msg)
        names += [name] if name else []
    if url and url.strip():
        msg, name = _run_ingest(url.strip())
        msgs.append(msg)
        names += [name] if name else []
    return ("\n".join(msgs) or "Nothing to add."), *refresh(names)


def remove_source(name, also_file):
    if not name:
        return "Choose a file to remove first.", *refresh()
    remove(name, also_file)
    return f"Removed {name}.", *refresh()


def ask(question, scope, history):
    history = list(history or [])
    if not question or not question.strip():
        return note("Type a question first."), show([]), "", history, gr.Dropdown(choices=history, value=None)
    q = question.strip()
    history = ([q] + [x for x in history if x != q])[:20]
    recent = gr.Dropdown(choices=history, value=None)
    try:
        text, hits = answer(q, sources=scope or None)
    except Exception as e:
        return note(f"Something went wrong: {e}"), show([]), "", history, recent
    if "not found in the sources" in text.lower():
        return render_answer(text) + ocr_hint(scope), show([]), "", history, recent
    known, rows = load_sources(), []
    for h in hits:
        label = html.escape(cite(h).strip("[]"))
        link = link_for(h, known)
        name = f'<a href="{html.escape(link)}" target="_blank">{label}</a>' if link else f"<b>{label}</b>"
        rows.append(f'<div class="src">{name}<em>score {h["score"]:.1f}</em>'
                    f'<p>{html.escape(h["content"][:170])}…</p></div>')
    return render_answer(text), show(evidence(hits)), "".join(rows), history, recent

def delete_one(selected, history):
    history = [x for x in (history or []) if x != selected]
    return history, gr.Dropdown(choices=history, value=None)


# ---------------------------------------------------------------- layout
takes_css = "css" in inspect.signature(gr.Blocks.__init__).parameters   # differs between Gradio versions
style = dict(theme=THEME, css=CSS, js=JS)

with gr.Blocks(title="SourceLens", **(style if takes_css else {})) as demo:
    gr.HTML(HERO)
    stats = gr.HTML(stats_html)
    history = gr.State([])
    with gr.Row():
        with gr.Column(scale=4):
            files = gr.File(label="Add files (PDF, video, image)", file_count="multiple")
            url = gr.Textbox(label="...or a video link", placeholder="https://...")
            add = gr.Button("Add to library", variant="primary")
            status = gr.Textbox(label="Status", interactive=False, lines=3)
            library = gr.HTML(library_html)
            with gr.Accordion("Remove from library", open=False):
                rm_pick = gr.Dropdown(choices=source_names(), value=None, label="Choose a source")
                rm_file = gr.Checkbox(label="Also delete the saved file from the data folder")
                rm_btn = gr.Button("Remove", variant="secondary")
        with gr.Column(scale=7):
            scope = gr.Dropdown(choices=source_names(), value=[], multiselect=True, elem_id="scope-dd",
                                label="Search only in (empty = all files)")
            question = gr.Textbox(label="Your question", lines=1,
                                  placeholder="e.g. What does the professor say about staying silent?")
            with gr.Row():
                go = gr.Button("Ask", variant="primary", scale=3)
                clear = gr.Button("Clear", variant="secondary", scale=1)
            ans = gr.HTML(elem_classes=["flat"])
            gallery = gr.Gallery(label="Evidence (source pages and frames)", columns=3, height=340, visible=False)
            srcs = gr.HTML(elem_classes=["flat"])
            with gr.Accordion("Recent questions", open=False, elem_classes=["recent-questions"] ):
                recent = gr.Dropdown(choices=[], value=None, label="Click one to reuse it")
                with gr.Row():
                    del_btn = gr.Button("Delete this question", variant="secondary")
                    del_all = gr.Button("Delete all", variant="secondary")

    synced = [stats, library, scope, rm_pick]
    add.click(add_sources, [files, url], [status, *synced])
    rm_btn.click(remove_source, [rm_pick, rm_file], [status, *synced])
    # for trigger in (go.click, question.submit):
    #     trigger(ask, [question, scope, history], [ans, gallery, srcs, history, recent])
    for trigger in (go.click, question.submit):
        trigger(ask, [question, scope, history], [ans, gallery, srcs, history, recent],show_progress="full", scroll_to_output=True)
    clear.click(lambda: ("", "", show([]), ""), None, [question, ans, gallery, srcs])
    recent.change(lambda q: gr.update(value=q) if q else gr.update(), recent, question)
    del_btn.click(delete_one, [recent, history], [history, recent])
    del_all.click(lambda: ([], gr.Dropdown(choices=[], value=None)), None, [history, recent])

demo.launch(**({} if takes_css else style))
