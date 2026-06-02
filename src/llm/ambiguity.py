"""Lightweight ambiguity scoring for selective rewrite."""

from __future__ import annotations

from dataclasses import dataclass, field


AGE_WORDS = {"boy", "girl", "child", "kid", "baby", "mother", "father"}
COUNT_WORDS = {"group", "crowd", "two", "three", "several", "many", "one", "single"}
SCENE_WORDS = {"street", "room", "kitchen", "park", "stage", "outdoor", "indoor"}


@dataclass
class AmbiguityResult:
    score: float
    trigger: bool
    reasons: list[str] = field(default_factory=list)
    token_count: int = 0
    query: str = ""
    lexical_score: float = 0.0
    retrieval_uncertainty_score: float = 0.0
    policy: str = "baseline"
    retrieval_features: dict = field(default_factory=dict)



def _lexical_signal(tokens: list[str]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    if len(tokens) <= 3:
        score += 0.25
        reasons.append("short_query")
    if any(tok in AGE_WORDS for tok in tokens):
        score += 0.20
        reasons.append("age_sensitive")
    if any(tok in COUNT_WORDS for tok in tokens):
        score += 0.20
        reasons.append("count_sensitive")
    if any(tok in SCENE_WORDS for tok in tokens):
        score += 0.10
        reasons.append("scene_constraint")
    return min(score, 1.0), reasons



def _retrieval_signal(retrieval_scores: list[float] | None) -> tuple[float, dict, list[str]]:
    if not retrieval_scores:
        return 0.0, {}, []
    top1 = retrieval_scores[0]
    top2 = retrieval_scores[1] if len(retrieval_scores) > 1 else retrieval_scores[0]
    margin = top1 - top2
    score = 0.0
    reasons: list[str] = []
    if top1 < 0.24:
        score += 0.20
        reasons.append("low_top1")
    if margin < 0.02:
        score += 0.25
        reasons.append("small_margin")
    return min(score, 1.0), {"top1": top1, "top2": top2, "margin": margin}, reasons



def score_query_ambiguity(
    query: str,
    threshold: float = 0.4,
    retrieval_scores: list[float] | None = None,
) -> AmbiguityResult:
    tokens = [tok.strip(' ,.!?').lower() for tok in query.split() if tok.strip()]
    lexical_score, lexical_reasons = _lexical_signal(tokens)
    retrieval_score, retrieval_features, retrieval_reasons = _retrieval_signal(retrieval_scores)
    score = min(1.0, lexical_score + retrieval_score)
    reasons = lexical_reasons + retrieval_reasons
    policy = "riskaware_light" if score >= threshold else "baseline"
    return AmbiguityResult(
        score=score,
        trigger=score >= threshold,
        reasons=reasons,
        token_count=len(tokens),
        query=query,
        lexical_score=lexical_score,
        retrieval_uncertainty_score=retrieval_score,
        policy=policy,
        retrieval_features=retrieval_features,
    )
