from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.utils.cache_utils import make_cache_key, load_json_cache, save_json_cache

if TYPE_CHECKING:
    from src.llm.client import OpenAIClient


RERANK_PROMPT_VERSION = "v2_semantic"


def build_rerank_system_prompt() -> str:
    return (
        "You are helping rerank retrieved video candidates for a text-to-video retrieval system.\n"
        "You will receive an original user query, a rewritten query used for retrieval, "
        "and a candidate video's visual semantic summary.\n"
        "Use the rewritten query as the main retrieval-oriented reference, "
        "but preserve the original user intent from the original query.\n"
        "Judge how relevant the candidate is to the query.\n"
        "Return a relevance score from 0 to 100.\n"
        "Do not invent content that is not provided.\n"
        "Be conservative and consistent."
    )


def build_rerank_user_prompt(
    query: str,
    rewritten_query: str | None,
    candidate: dict,
) -> str:
    rewritten_query = rewritten_query or query
    summary = candidate.get("semantic_summary", "")
    tags = candidate.get("semantic_tags", [])

    return (
        f"Original query: {query}\n"
        f"Rewritten query: {rewritten_query}\n"
        f"Candidate rank: {candidate['rank']}\n"
        f"Candidate retrieval score: {candidate['retrieval_score']:.4f}\n"
        f"Candidate segment time: {candidate['start_sec']:.2f} to {candidate['end_sec']:.2f} seconds\n"
        f"Candidate visual summary: {summary}\n"
        f"Candidate visual tags: {', '.join(tags)}\n\n"
        "Please output exactly in the following format:\n"
        "score: <0-100 integer>\n"
        "reason: <one short sentence>"
    )


def parse_rerank_output(text: str) -> dict:
    score = 50
    reason = ""

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        if low.startswith("score:"):
            try:
                score = int(ln.split(":", 1)[1].strip())
            except Exception:
                score = 50
        elif low.startswith("reason:"):
            reason = ln.split(":", 1)[1].strip()

    score = max(0, min(100, score))
    return {"score": score, "reason": reason}


def rerank_candidate_with_cache(
    query: str,
    rewritten_query: str | None,
    candidate: dict,
    client: OpenAIClient,
    cache_dir: str | Path,
) -> dict:
    key_payload = {
        "task": "rerank",
        "model": client.model,
        "prompt_version": RERANK_PROMPT_VERSION,
        "query": query,
        "rewritten_query": rewritten_query,
        "candidate": {
            "video_id": candidate["video_id"],
            "segment_id": candidate["segment_id"],
            "start_sec": round(float(candidate["start_sec"]), 3),
            "end_sec": round(float(candidate["end_sec"]), 3),
            "retrieval_score": round(float(candidate["retrieval_score"]), 6),
            "rank": int(candidate["rank"]),
            "semantic_summary": candidate.get("semantic_summary", ""),
            "semantic_tags": candidate.get("semantic_tags", []),
        },
    }

    cache_key = make_cache_key(key_payload)
    cached = load_json_cache(cache_dir, cache_key)
    if cached is not None:
        cached["cache_hit"] = True
        return cached

    resp = client.generate_text(
        system_prompt=build_rerank_system_prompt(),
        user_prompt=build_rerank_user_prompt(
            query=query,
            rewritten_query=rewritten_query,
            candidate=candidate,
        ),
        temperature=0.0,
        max_output_tokens=80,
    )

    parsed = parse_rerank_output(resp.text)

    result = {
        "video_id": candidate["video_id"],
        "segment_id": candidate["segment_id"],
        "llm_score": parsed["score"],
        "reason": parsed["reason"],
        "cache_hit": False,
        "model": client.model,
        "prompt_version": RERANK_PROMPT_VERSION,
        "usage": {
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "total_tokens": resp.total_tokens,
        },
        "retrieval_rank": candidate["rank"],
        "retrieval_score": candidate["retrieval_score"],
        "start_sec": candidate["start_sec"],
        "end_sec": candidate["end_sec"],
        "semantic_summary": candidate.get("semantic_summary", ""),
        "semantic_tags": candidate.get("semantic_tags", []),
    }

    save_json_cache(cache_dir, cache_key, result)
    return result
