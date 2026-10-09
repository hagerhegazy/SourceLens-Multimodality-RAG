import json, os, re, time
import pymupdf
import config
from retrieval import retrieve

K = 6
CONFIGS = {
    "dense only":           dict(use_bm25=False, use_rerank=False),
    "BM25 only":            dict(use_dense=False, use_rerank=False),
    "hybrid (RRF)":         dict(use_rerank=False),
    "dense + rerank":       dict(use_bm25=False),
    "hybrid + rerank":      dict(),
}

def norm(s):
    return re.sub(r"\s+", " ", s).lower()

_pages = {}
def pdf_pages(source):
    if source not in _pages:
        doc = pymupdf.open(os.path.join("data", source))
        _pages[source] = [norm(p.get_text()) for p in doc]
    return _pages[source]

def resolve(e):
    """Turn an expected entry into {source, set of acceptable locations, modality}."""
    mod = e.get("modality")
    if "phrase" in e:
        pages = {i for i, t in enumerate(pdf_pages(e["source"]), 1)
                 if norm(e["phrase"]) in t}
        if not pages:
            print(f"WARNING: phrase not found in {e['source']}: {e['phrase']!r}")
        return {"source": e["source"], "pages": pages, "modality": mod}
    tol = e.get("tolerance", 0)
    return {"source": e["source"],
            "pages": set(range(e["location"] - tol, e["location"] + tol + 1)),
            "modality": mod}

ALIASES = config.EVAL_ALIASES

def matches(r, e):
    same_source = r["source"] == e["source"] or r["source"] in ALIASES.get(e["source"], [])
    return (same_source and int(r["location"]) in e["pages"]
            and (not e["modality"] or r["modality"] == e["modality"]))

raw = json.load(open("eval/questions.json", encoding="utf-8"))
questions, unanswerable, skipped = [], 0, 0
for q in raw:
    if not q["expected"]:
        unanswerable += 1          # "Not found" questions are checked by hand
        continue
    exp = [x for x in map(resolve, q["expected"]) if x["pages"]]
    if not exp:
        skipped += 1
        print("SKIPPED (nothing resolved):", q["question"])
        continue
    questions.append({"question": q["question"], "expected": exp})

print(f"Loaded {len(raw)} entries: {len(questions)} scored, "
      f"{unanswerable} unanswerable, {skipped} skipped\n")
if not questions:
    raise SystemExit("No scored questions. Check eval/questions.json: valid JSON, "
                     "'expected' filled in, file names match the ones in data/.")

def ranks(**opts):
    out, total = [], 0.0
    for q in questions:
        start = time.perf_counter()
        results = retrieve(q["question"], k=K, **opts)[:K]
        total += time.perf_counter() - start
        out.append(next((i for i, r in enumerate(results, 1)
                         if any(matches(r, e) for e in q["expected"])), None))
    return out, 1000 * total / len(questions)

retrieve("warm up")                # load models first so timings are fair
all_ranks, latency = {}, {}
for name, opts in CONFIGS.items():
    all_ranks[name], latency[name] = ranks(**opts)

lines = [f"{len(questions)} questions, k={K}", "",
         f"| configuration | hit@{K} | MRR | ms/query |", "|----------|------------|-----------|--------------||---------------||----------------||---------------------|"]
for name, rk in all_ranks.items():
    hit = sum(r is not None for r in rk) / len(rk)
    mrr = sum(1 / r for r in rk if r) / len(rk)
    lines.append(f"| {name} | {hit:.2f} | {mrr:.2f} | {latency[name]:.0f} |")

lines += ["", "Rank of first correct result per question (- = miss):", "",
          "| question | " + " | ".join(CONFIGS) + " |",
          "|---|" + "---|" * len(CONFIGS)]
for i, q in enumerate(questions):
    cells = [str(all_ranks[n][i] or "-") for n in CONFIGS]
    lines.append(f"| {q['question'][:50]} | " + " | ".join(cells) + " |")

report = "\n".join(lines)
print(report)
open("eval/results.md", "w", encoding="utf-8").write(report)