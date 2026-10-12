"""Grounding RAG helper: chunk -> embed (homelab Ollama) -> Chroma (local) -> retrieve."""
import os
import re
import requests
import chromadb
from chromadb.config import Settings

DATA_DIR = os.getenv("DATA_DIR", "/data")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.1.42:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "embeddinggemma:latest")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
TEXT_DIR = os.path.join(DATA_DIR, "texts")
os.makedirs(TEXT_DIR, exist_ok=True)


def _client():
    return chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))


def _collection(nb_id):
    return _client().get_or_create_collection(name=f"nb_{nb_id}")


def embed(texts):
    r = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["embeddings"]


def chunk_text(text, size=800, overlap=120):
    text = re.sub(r"\n{3,}", "\n\n", text)
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += size - overlap
    return chunks or [""]


def save_text(source_id, text):
    with open(os.path.join(TEXT_DIR, source_id + ".txt"), "w", encoding="utf-8") as f:
        f.write(text)


def load_text(source_id):
    p = os.path.join(TEXT_DIR, source_id + ".txt")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def index(nb_id, source_id, source_name, text):
    chunks = chunk_text(text)
    embs = embed(chunks)
    coll = _collection(nb_id)
    coll.upsert(
        ids=[f"{source_id}::{j}" for j in range(len(chunks))],
        documents=chunks,
        embeddings=embs,
        metadatas=[{"source_id": source_id, "name": source_name} for _ in chunks],
    )
    save_text(source_id, text)
    return len(chunks)


def delete_source(nb_id, source_id):
    coll = _collection(nb_id)
    res = coll.get(where={"source_id": source_id})
    ids = res.get("ids", [])
    if ids:
        coll.delete(ids=ids)
    p = os.path.join(TEXT_DIR, source_id + ".txt")
    if os.path.exists(p):
        os.remove(p)


def retrieve(nb_id, query, top_k=6):
    coll = _collection(nb_id)
    if coll.count() == 0:
        return []
    q = embed([query])[0]
    res = coll.query(query_embeddings=[q], n_results=min(top_k, coll.count()))
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({"text": doc, "name": meta["name"], "source_id": meta["source_id"], "distance": dist})
    return out


def retrieve_by_source(nb_id, source_id, query, top_k=4):
    coll = _collection(nb_id)
    if coll.count() == 0:
        return []
    q = embed([query])[0]
    try:
        res = coll.query(query_embeddings=[q], n_results=min(top_k, coll.count()), where={"source_id": source_id})
    except Exception:  # chroma where not supported / empty
        return []
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({"text": doc, "distance": dist})
    return out


def all_source_texts(nb_id):
    """Full text of every source in a notebook (for guide/summary generation)."""
    coll = _collection(nb_id)
    seen = {}
    res = coll.get(include=["metadatas", "documents"])
    for doc, meta in zip(res.get("documents", []), res.get("metadatas", [])):
        sid = meta["source_id"]
        if sid not in seen:
            seen[sid] = {"name": meta["name"], "text": load_text(sid)}
    return list(seen.values())