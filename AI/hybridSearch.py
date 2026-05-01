import os
from datetime import datetime

import chromadb
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from rank_bm25 import BM25Okapi

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_base = os.getenv("METIS_OPENAI_BASE_URL")
if not _base:
    raise RuntimeError("METIS_OPENAI_BASE_URL is not set")

openai_client = OpenAI(
    api_key=os.getenv("METIS_API_KEY"),
    base_url=_base.rstrip("/"),
)

_root = os.path.dirname(__file__)
_chroma = os.path.join(_root, "chroma_db")
client = chromadb.PersistentClient(path=_chroma)
collection = client.get_collection(name="binance_help_docs")


def tokenize_persian(text):
    return text.split()


def bm25_search(query, all_docs, all_ids, top_k=10):
    tokenized_docs = [tokenize_persian(doc) for doc in all_docs]
    bm25 = BM25Okapi(tokenized_docs)
    tokenized_query = tokenize_persian(query)
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(all_ids[i], scores[i]) for i in top_indices]


def reciprocal_rank_fusion(semantic_results, bm25_results, k=60):
    scores = {}
    for rank, (doc_id, _) in enumerate(semantic_results, 1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    for rank, (doc_id, _) in enumerate(bm25_results, 1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


out = "hybrid_search_results.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write(f"{datetime.now().isoformat()}\n\n")
    q = "اهرمی"
    print(q)
    f.write(f"q={q}\n\n")

    all_data = collection.get()
    all_docs = all_data["documents"]
    all_ids = all_data["ids"]

    emb = openai_client.embeddings.create(
        input=q,
        model="text-embedding-3-small",
        encoding_format="float",
    )
    qv = emb.data[0].embedding
    sem = collection.query(query_embeddings=[qv], n_results=10)
    sem_rank = list(zip(sem["ids"][0], sem["distances"][0]))
    bm25_rank = bm25_search(q, all_docs, all_ids, top_k=10)
    hybrid_rank = reciprocal_rank_fusion(sem_rank, bm25_rank)

    doc_map = {doc_id: doc for doc_id, doc in zip(all_ids, all_docs)}
    for i, (doc_id, rrf_score) in enumerate(hybrid_rank[:3], 1):
        snippet = doc_map.get(doc_id, "")[:300]
        f.write(f"{i} {doc_id} rrf={rrf_score:.4f}\n{snippet}\n\n")
        print(i)

print(out)
