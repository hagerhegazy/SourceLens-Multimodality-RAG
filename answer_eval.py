import json, os, re, sys, time
import pymupdf
from groq import Groq
import config
from query import answer, cite

ALIASES = config.EVAL_ALIASES
JUDGE_MODEL = os.getenv("JUDGE_MODEL", config.LLM_MODEL)
PAUSE = float(os.getenv("EVAL_SLEEP", "3"))          # seconds between questions (rate limits)
STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # 3 = every 3rd answerable question

def norm(s):
    return re.sub(r"\s+", " ", s).lower()

_pages = {}
def pdf_pages(source):
    if source not in _pages:
        doc = pymupdf.open(os.path.join("data", source))
        _pages[source] = [norm(p.get_text()) for p in doc]
    return _pages[source]

def resolve(e):
    mod = e.get("modality")
    if "phrase" in e:
        pages = {i for i, t in enumerate(pdf_pages(e["source"]), 1) if norm(e["phrase"]) in t}
        return {"source": e["source"], "pages": pages, "modality": mod}
    tol = e.get("tolerance", 0)
    return {"source": e["source"],
            "pages": set(range(e["location"] - tol, e["location"] + tol + 1)),
            "modality": mod}

def matches(r, e):
    same = r["source"] == e["source"] or r["source"] in ALIASES.get(e["source"], [])
    return (same and int(r["location"]) in e["pages"]
            and (not e["modality"] or r["modality"] == e["modality"]))

def retry(fn, tries=5):
    for i in range(tries):
        try:
            return fn()
        except Exception as ex:
            wait = 15 * (i + 1)
            print(f"   retrying in {wait}s ({str(ex)[:70]})")
            time.sleep(wait)
    raise SystemExit("Giving up: the API kept failing.")

def judge(question, hits, ans):
    ctx = "\n".join(f"{cite(h)}: {h['content']}" for h in hits)
    prompt = ("You are a strict fact checker. Read the SOURCES and the ANSWER. "
              "Reply with exactly one word: SUPPORTED if every factual claim in the ANSWER "
              "is backed by the SOURCES, otherwise UNSUPPORTED.\n\n"
              f"SOURCES:\n{ctx}\n\nQUESTION: {question}\n\nANSWER: {ans}")
    r = Groq(api_key=config.GROQ_API_KEY).chat.completions.create(
        model=JUDGE_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
    verdict = (r.choices[0].message.content or "").upper()
    return "UNSUPPORTED" not in verdict and "SUPPORTED" in verdict

raw = json.load(open("eval/questions.json", encoding="utf-8"))
rows = []
for i, q in enumerate(raw):
    if q["expected"] and i % STEP:
        continue
    ans, hits = retry(lambda: answer(q["question"]))
    refused = "not found in the sources" in ans.lower()
    row = {"q": q["question"], "answerable": bool(q["expected"]), "refused": refused}
    if q["expected"]:
        exp = [resolve(e) for e in q["expected"]]
        row["cited"] = any(cite(h).strip("[]") in ans and any(matches(h, e) for e in exp)
                           for h in hits)
        kws = q.get("answer_any")
        row["keyword"] = None if not kws else any(k.lower() in ans.lower() for k in kws)
        row["supported"] = None if refused else retry(lambda: judge(q["question"], hits, ans))
    rows.append(row)
    print(("REFUSED " if refused else "ANSWERED"), "|", q["question"][:70])
    time.sleep(PAUSE)

def count(rs, key):
    vals = [r[key] for r in rs if r.get(key) is not None]
    return f"{sum(vals)}/{len(vals)}"

good = [r for r in rows if r["answerable"]]
bad = [r for r in rows if not r["answerable"]]
lines = [f"Judge model: {JUDGE_MODEL}", "",
         "| check | result |", "|---|---|",
         f"| answerable questions answered | {sum(not r['refused'] for r in good)}/{len(good)} |",
         f"| answer cites a correct source | {count(good, 'cited')} |",
         f"| claims supported by the retrieved text | {count(good, 'supported')} |",
         f"| expected keyword present | {count(good, 'keyword')} |",
         f"| unanswerable questions refused | {sum(r['refused'] for r in bad)}/{len(bad)} |",
         "", "| question | answered | cited | supported | keyword |", "|---|---|---|---|---|"]
sym = {True: "yes", False: "NO", None: "-"}
for r in good:
    lines.append(f"| {r['q'][:50]} | {sym[not r['refused']]} | {sym[r['cited']]} | "
                 f"{sym[r['supported']]} | {sym[r['keyword']]} |")
for r in bad:
    lines.append(f"| {r['q'][:50]} | refused: {sym[r['refused']]} | | | |")

report = "\n".join(lines)
print("\n" + report)
open("eval/answer_results.md", "w", encoding="utf-8").write(report)