"""Shared index: every PDF chunk, frame caption, speech chunk and image caption is one record."""
import chromadb
from sentence_transformers import SentenceTransformer
import config

_model = None
def _embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model

def _col():
    client = chromadb.PersistentClient(path=config.DB_DIR)
    return client.get_or_create_collection("knowledge", metadata={"hnsw:space": "cosine"})

# record = {id, modality: text|frame|speech|image, content, source, location, thumb}
# location = page number (pdf) or seconds (video)
def add_records(records):
    if not records:
        return
    texts = [r["content"] for r in records]
    embs = _embedder().encode(texts, normalize_embeddings=True).tolist()
    _col().upsert(
        ids=[r["id"] for r in records],
        documents=texts,
        embeddings=embs,
        metadatas=[{k: r[k] for k in ("modality", "source", "location", "thumb")} for r in records],
    )

def search(query, k=config.TOP_K, modality=None, sources=None):
    emb = _embedder().encode([query], normalize_embeddings=True).tolist()
    conds = []
    if modality:
        conds.append({"modality": modality})
    if sources:
        conds.append({"source": {"$in": list(sources)}})
    where = None if not conds else (conds[0] if len(conds) == 1 else {"$and": conds})
    res = _col().query(query_embeddings=emb, n_results=k, where=where)
    return [
        {"id": i, "content": d, **m}
        for i, d, m in zip(res["ids"][0], res["documents"][0], res["metadatas"][0])
    ]
def delete_source(name):
    _col().delete(where={"source": name})