"""
RAG DDI — Retrieval-Augmented Generation for Drug-Drug Interactions.
Queries a ChromaDB vector store of DDI records using Ollama nomic-embed-text.
"""

import os
import requests

_client = None
_collection = None

DB_PATH = os.environ.get("DDI_DB_PATH", "/app/ddi_chromadb")
COLLECTION_NAME = "ddi_interactions"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

# Embeds compete with the 28GB mixtral for the GPU. Give the call room (the old
# 15s timed out while mixtral cold-loaded) and pin nomic-embed-text resident so
# Ollama doesn't unload it between queries and force a cold reload.
EMBED_TIMEOUT = 60
EMBED_KEEP_ALIVE = -1
EMBED_RETRIES = 1


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    import chromadb
    _client = chromadb.PersistentClient(path=DB_PATH)
    _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def _embed(text: str) -> list[float]:
    last_exc = None
    for attempt in range(EMBED_RETRIES + 1):
        try:
            resp = requests.post(
                OLLAMA_EMBED_URL,
                json={"model": EMBED_MODEL, "prompt": text, "keep_alive": EMBED_KEEP_ALIVE},
                timeout=EMBED_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception as e:
            last_exc = e
            print(f"[rag_ddi] embed attempt {attempt + 1}/{EMBED_RETRIES + 1} failed: {e}")
    raise last_exc


def retrieve_interaction(drug1: str, drug2: str, n_results: int = 5) -> dict:
    """Retrieve closest DDI records for a drug pair."""
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return {"available": False}
    except Exception:
        return {"available": False}

    query_text = f"Drug interaction: {drug1} + {drug2}"
    try:
        embedding = _embed(query_text)
    except Exception:
        return {"available": False}

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        hit = {
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": round(distance, 4),
            "exact_match": distance < 0.30,
        }
        hits.append(hit)
        # DEBUG
        m = hit["metadata"]
        print(f"[rag_ddi] hit {i}: {m.get('drug_a')} + {m.get('drug_b')} | severity={m.get('severity')} | dist={hit['distance']} | exact={hit['exact_match']}")

    return {"available": True, "hits": hits}


def format_rag_context(results: dict) -> str:
    """Format retrieval results into a prompt-injectable context block."""
    if not results.get("available") or not results.get("hits"):
        return ""

    lines = ["REFERENCE DATA (from clinical DDI database):"]
    for hit in results["hits"]:
        m = hit["metadata"]
        lines.append(
            f"- {m.get('drug_a', '?')} + {m.get('drug_b', '?')}: "
            f"Severity={m.get('severity', '?')}. "
            f"Mechanism: {m.get('mechanism', 'N/A')}. "
            f"Management: {m.get('management', 'N/A')}. "
            f"Alternatives: {m.get('alternatives', 'N/A')}."
        )
    return "\n".join(lines)


def warm_up(probe_pair: tuple[str, str] = ("warfarin", "aspirin")) -> bool:
    """Prime RAG so the first real query can't cold-fail.

    (a) Dummy embed → loads nomic-embed-text into Ollama and pins it resident
        (keep_alive=-1), so it's already warm when the 28GB mixtral later
        cold-loads and saturates the GPU.
    (b) Dummy retrieve → opens the Chroma collection and builds its HNSW index.

    Returns True only if BOTH succeed (caller sets RAG_READY from this).
    """
    try:
        _embed("warm-up")
    except Exception as e:
        print(f"[rag_ddi] warm-up embed failed: {e}")
        return False
    try:
        res = retrieve_interaction(probe_pair[0], probe_pair[1])
    except Exception as e:
        print(f"[rag_ddi] warm-up retrieve raised: {e}")
        return False
    if not res.get("available"):
        print("[rag_ddi] warm-up retrieve returned available=False")
        return False
    print("[rag_ddi] warm-up OK — embed primed (resident) + collection ready")
    return True
