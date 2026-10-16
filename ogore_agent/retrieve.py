"""Deterministic retrieval: local sentence embeddings (CPU), cosine similarity, top-k with a stable tie-break."""
import numpy as np

from .config import EMBED_MODEL, EMBED_REVISION

_model = None


def _encoder(model=EMBED_MODEL, revision=EMBED_REVISION):
    global _model
    if _model is None:
        import torch
        from sentence_transformers import SentenceTransformer
        torch.use_deterministic_algorithms(True)
        _model = SentenceTransformer(model, revision=revision, device="cpu")
    return _model


def embed(texts):
    v = _encoder().encode(list(texts), batch_size=16, normalize_embeddings=True, convert_to_numpy=True)
    return np.round(v.astype(np.float64), 6)   # rounding removes last-bit noise across machines


def query_text(q):
    kpis = "; ".join(k["text"] for k in q["kpis"])
    return (f"IT goal: {q['goal']['text']}. Parent goal: {q['parent']['text']}. "
            f"Business domain: {q['domain']}. Organization type: {q['organization_type']}. KPIs: {kpis}.")


def top_k(query, chunks, k):
    qv = embed([query_text(query)])[0]
    cv = embed([c.text for c in chunks])
    scores = cv @ qv
    order = sorted(range(len(chunks)), key=lambda i: (-round(float(scores[i]), 4), chunks[i].chunk_id))
    return [(chunks[i], round(float(scores[i]), 4)) for i in order[:k]]
