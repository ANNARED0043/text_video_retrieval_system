"""Query rewrite helpers with cache support."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from src.llm.ambiguity import AmbiguityResult
from src.utils.cache_utils import load_json_cache, make_cache_key, save_json_cache

if TYPE_CHECKING:
    from src.llm.client import OpenAIClient


REWRITE_PROMPT_VERSION = "v2_riskaware"


def build_rewrite_system_prompt(riskaware: bool = False) -> str:
    base = (
        "You rewrite video retrieval queries.\n"
        "Your goal is to make the query more explicit and retrieval-friendly.\n"
        "Rules:\n"
        "1. Preserve the original intent.\n"
        "2. Do NOT invent specific facts that are not implied.\n"
        "3. Make the wording clearer and more visually grounded.\n"
        "4. Output exactly one rewritten query sentence.\n"
        "5. Do not explain your reasoning."
    )
    if not riskaware:
        return base
    return (
        base
        + "\n6. Be careful with age, count, relation, and scene constraints."
        + "\n7. Keep singular/plural and family-role wording whenever present."
    )


def build_rewrite_user_prompt(query: str, ambiguity: AmbiguityResult) -> str:
    reasons = ", ".join(ambiguity.reasons) if ambiguity.reasons else "none"
    return (
        f"Original query: {query}\n"
        f"Ambiguity score: {ambiguity.score:.3f}\n"
        f"Reasons: {reasons}\n\n"
        "Rewrite the query into a more specific, visually descriptive retrieval query."
    )


def rewrite_query_with_cache(
    query: str,
    ambiguity: AmbiguityResult,
    client: OpenAIClient,
    cache_dir: str | Path,
    force_rewrite: bool = False,
    riskaware: bool = False,
) -> dict:
    should_rewrite = force_rewrite or ambiguity.trigger
    if not should_rewrite:
        return {
            "original_query": query,
            "rewritten_query": query,
            "used_rewrite": False,
            "cache_hit": False,
            "model": None,
            "prompt_version": REWRITE_PROMPT_VERSION,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "ambiguity": asdict(ambiguity),
        }

    key_payload = {
        "task": "rewrite",
        "model": client.model,
        "prompt_version": REWRITE_PROMPT_VERSION,
        "query": query,
        "riskaware": riskaware,
    }
    cache_key = make_cache_key(key_payload)
    cached = load_json_cache(cache_dir, cache_key)
    if cached is not None:
        cached["cache_hit"] = True
        return cached

    resp = client.generate_text(
        system_prompt=build_rewrite_system_prompt(riskaware=riskaware),
        user_prompt=build_rewrite_user_prompt(query, ambiguity),
        temperature=0.0,
        max_output_tokens=80,
    )
    rewritten = resp.text.strip() or query
    result = {
        "original_query": query,
        "rewritten_query": rewritten,
        "used_rewrite": True,
        "cache_hit": False,
        "model": client.model,
        "prompt_version": REWRITE_PROMPT_VERSION,
        "usage": {
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "total_tokens": resp.total_tokens,
        },
        "ambiguity": asdict(ambiguity),
    }
    save_json_cache(cache_dir, cache_key, result)
    return result
