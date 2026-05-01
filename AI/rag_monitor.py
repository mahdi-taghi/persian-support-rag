"""
سبک‌وزن: سیگنال‌های retrieval و در صورت تمایل هم‌ترازی پاسخ با context.
بدون فریمورک سنگین؛ مناسب لاگ و مرور انسانی در ادمین.
"""

from __future__ import annotations

import math
import os
from typing import Any

# اگر هم‌نیاز بود کم کن؛ زیر آستانه = منابع بازیابی ضعیف‌تر از حد معمول
RRF_WEAK_THRESHOLD = float(os.getenv("AI_MONITOR_RRF_WEAK", "0.013"))
# شباهت embedding بین متن مرجع و پاسخ؛ زیر این = پیشنهاد بازبینی
ALIGNMENT_WEAK_THRESHOLD = float(os.getenv("AI_MONITOR_ALIGNMENT_WEAK", "0.32"))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _alignment_score(client, context_text: str, answer_text: str, model: str) -> float | None:
    ctx = (context_text or "")[:8000]
    ans = (answer_text or "")[:4000]
    if not ans.strip():
        return None
    r = client.embeddings.create(input=[ctx, ans], model=model, encoding_format="float")
    return _cosine(r.data[0].embedding, r.data[1].embedding)


def _hint(*, weak_sources: bool, alignment: float | None) -> str:
    if weak_sources:
        return "weak_retrieval"
    if alignment is not None and alignment < ALIGNMENT_WEAK_THRESHOLD:
        return "review_suggested"
    return "ok"


def monitor_skipped(path: str, detail: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"path": path, "hint": "n/a"}
    if detail:
        out["detail"] = detail
    return out


def monitor_rag_answer(
    *,
    hybrid_top3: list[tuple[str, float]],
    semantic_ranked: list[tuple[str, float]],
    context_text: str,
    answer_text: str,
    openai_client=None,
    embedding_model: str = "text-embedding-3-small",
) -> dict[str, Any]:
    """بعد از تولید پاسخ RAG فراخوانی شود."""
    sem_dist_by_id = {doc_id: float(dist) for doc_id, dist in semantic_ranked}
    ids = [doc_id for doc_id, _ in hybrid_top3]
    rrfs = [float(score) for _, score in hybrid_top3]
    top_rrf = rrfs[0] if rrfs else 0.0
    weak_sources = top_rrf < RRF_WEAK_THRESHOLD

    sem_top = None
    if ids:
        sem_top = sem_dist_by_id.get(ids[0])

    alignment_enabled = os.getenv("AI_MONITOR_ALIGNMENT", "").lower() in (
        "1",
        "true",
        "yes",
    )
    alignment: float | None = None
    if alignment_enabled and openai_client is not None:
        alignment = _alignment_score(
            openai_client, context_text, answer_text, embedding_model
        )

    hint = _hint(weak_sources=weak_sources, alignment=alignment)

    return {
        "path": "rag",
        "hint": hint,
        "retrieval": {
            "top_chunk_ids": ids,
            "rrf_scores": rrfs,
            "semantic_distance_top_chunk": sem_top,
            "weak_sources": weak_sources,
        },
        **({"alignment": {"context_answer_cosine": alignment}} if alignment is not None else {}),
    }
