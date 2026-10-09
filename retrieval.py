import re
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import config, store

_reranker = None
def _rerank_model():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(config.RERANK_MODEL)
    return _reranker

def _tok(text):
    return re.findall(r"\w+", text.lower())

def _bm25_search(query, k, modality, sources=None):
    data = store._col().get(include=["documents", "metadatas"])
    items = [{"id": i, "content": d, **m}
             for i, d, m in zip(data["ids"], data["documents"], data["metadatas"])]
    if modality:
        items = [x for x in items if x["modality"] == modality]
    if sources:
        items = [x for x in items if x["source"] in sources]
    if not items:
        return []
    bm = BM25Okapi([_tok(x["content"]) for x in items])
    scores = bm.get_scores(_tok(query))
    ranked = sorted(zip(scores, items), key=lambda p: -p[0])
    return [x for s, x in ranked[:k] if s > 0]

def _rrf(lists, k=60):
    """Reciprocal rank fusion: merge ranked lists by rank, not raw score."""
    scores, by_id = {}, {}
    for lst in lists:
        for rank, item in enumerate(lst):
            scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)
            by_id[item["id"]] = item
    return [by_id[i] for i in sorted(scores, key=scores.get, reverse=True)]

def retrieve(query, k=config.TOP_K, modality=None, candidates=20,
             use_dense=True, use_bm25=True, use_rerank=True, sources=None):
    lists = []
    if use_dense:
        lists.append(store.search(query, k=candidates, modality=modality, sources=sources))
    if use_bm25:
        lists.append(_bm25_search(query, candidates, modality, sources))
    fused = _rrf(lists)[:candidates]
    if not fused:
        return []
    if not use_rerank:
        return [dict(x, score=0.0) for x in fused[:k]]

    scores = _rerank_model().predict([(query, x["content"]) for x in fused])
    ranked = sorted(zip(scores, fused), key=lambda p: -p[0])
    top = [dict(x, score=float(s)) for s, x in ranked[:k] if s >= config.MIN_SCORE]
    # safety net: the top 2 results from the dense+BM25 fusion are always kept
    score_by_id = {x["id"]: float(s) for s, x in ranked}
    seen = {x["id"] for x in top}
    for x in fused[:2]:
        if x["id"] not in seen:
            top.append(dict(x, score=score_by_id[x["id"]]))
    return top