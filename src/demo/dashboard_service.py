"""Helpers for the Streamlit demo, summaries, search, and learning panels."""

from __future__ import annotations

import json
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from src.config import load_config
from src.features.clip_encoder import encode_text
from src.learning.text_adapter import AdapterTrainingConfig, RetrievalLearningDataset, TextResidualAdapter
from src.learning.text_adapter import _alignment_bonus, _memory_augmented_bonus
from src.llm.ambiguity import score_query_ambiguity
from src.llm.semantic_memory import load_semantic_memory


DATASETS = {
    "msrvtt_1ka": {
        "label": "MSR-VTT 1kA",
        "queries": "msrvtt_1kA_test_queries.jsonl",
        "manifest": "msrvtt_fixed_1kA.jsonl",
    }
}


def _queries_path(dataset_key: str) -> Path:
    cfg = load_config()
    rel = DATASETS[dataset_key]["queries"]
    return cfg.paths.data_dir / "annotations" / "msrvtt" / rel


def _manifest_path(dataset_key: str) -> Path:
    cfg = load_config()
    rel = DATASETS[dataset_key]["manifest"]
    return cfg.paths.manifests_dir / rel


def _index_dir(dataset_key: str, model_name: str, pretrained: str, pooling: str = "mean") -> Path:
    cfg = load_config()
    rel = DATASETS[dataset_key]["manifest"]
    model_suffix = f"{model_name}_{pretrained}".replace("/", "_")
    return cfg.paths.data_dir / "indexes" / rel.replace(".jsonl", "") / pooling / model_suffix / "flat_ip"


def _read_text_safely(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "gbk"):
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


def _read_json_safely(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(_read_text_safely(path))
    except Exception:
        return None


def _read_jsonl_safely(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in _read_text_safely(path).splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _load_manifest_rows(dataset_key: str) -> list[dict[str, Any]]:
    return _read_jsonl_safely(_manifest_path(dataset_key))


def _manifest_by_segment(dataset_key: str) -> dict[str, dict[str, Any]]:
    rows = _load_manifest_rows(dataset_key)
    return {str(row.get("segment_id")): row for row in rows if row.get("segment_id")}


def _manifest_by_video(dataset_key: str) -> dict[str, dict[str, Any]]:
    rows = _load_manifest_rows(dataset_key)
    video_rows: dict[str, dict[str, Any]] = {}
    for row in rows:
        video_id = str(row.get("video_id", ""))
        if not video_id or video_id in video_rows:
            continue
        video_rows[video_id] = row
    return video_rows


def list_datasets() -> dict[str, dict[str, str]]:
    return DATASETS


def load_queries(dataset_key: str) -> list[dict[str, Any]]:
    path = _queries_path(dataset_key)
    rows = _read_jsonl_safely(path)
    for idx, row in enumerate(rows):
        row.setdefault("qid", idx)
    return rows


def get_query_record(dataset_key: str, qid: int) -> dict[str, Any] | None:
    for row in load_queries(dataset_key):
        if int(row.get("qid", -1)) == int(qid):
            return row
    return None


def get_random_query(dataset_key: str, seed: int = 0) -> dict[str, Any] | None:
    rows = load_queries(dataset_key)
    if not rows:
        return None
    rng = random.Random(seed)
    return rng.choice(rows)


def build_summary_table() -> list[dict[str, Any]]:
    cfg = load_config()
    out_dir = cfg.paths.project_root / "outputs" / "tables"
    if not out_dir.exists():
        return []

    rows: list[dict[str, Any]] = []
    candidates = list(sorted(out_dir.glob("*summary.json")))
    analysis_dir = out_dir / "analysis"
    if analysis_dir.exists():
        candidates.extend(sorted(analysis_dir.glob("*.json")))

    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        payload = _read_json_safely(path)
        if not isinstance(payload, dict):
            continue
        metrics = payload.get("metrics", {})
        if all(payload.get(k, metrics.get(k)) is None for k in ("R@1", "R@5", "R@10")):
            continue
        rows.append(
            {
                "file": path.relative_to(cfg.paths.project_root).as_posix(),
                "mode": payload.get("mode") or payload.get("rerank_mode") or "unknown",
                "R@1": payload.get("R@1", metrics.get("R@1")),
                "R@5": payload.get("R@5", metrics.get("R@5")),
                "R@10": payload.get("R@10", metrics.get("R@10")),
                "MnR": payload.get("MnR", metrics.get("MnR")),
            }
        )
    return rows


def load_learning_snapshot() -> dict[str, Any]:
    cfg = load_config()
    analysis_dir = cfg.paths.project_root / "outputs" / "tables" / "analysis"
    feedback_dir = cfg.paths.project_root / "outputs" / "feedback"

    policy_hints = _read_json_safely(analysis_dir / "policy_hints.json")
    semantic_memory = _read_json_safely(analysis_dir / "semantic_memory.json")
    semantic_report = _read_json_safely(analysis_dir / "semantic_memory_report.json")
    diary_rows = _read_jsonl_safely(feedback_dir / "learning_diary.jsonl")
    research_candidates = [
        analysis_dir / "teacher_selection_and_r60_plan_2026-03-23.md",
        analysis_dir / "stage_execution_and_ablation_2026-03-23.md",
        analysis_dir / "agent_teacher_memory_plan_2026-03-23.md",
        analysis_dir / "learning_research_notes.md",
    ]
    research_notes_path = next((path for path in research_candidates if path.exists()), analysis_dir / "learning_research_notes.md")

    diary_counter = Counter(str(row.get("event_type", "unknown")) for row in diary_rows)

    return {
        "policy_hints": policy_hints if isinstance(policy_hints, dict) else {},
        "semantic_memory": semantic_memory if isinstance(semantic_memory, dict) else {},
        "semantic_report": semantic_report if isinstance(semantic_report, dict) else {},
        "prototype_memory": (semantic_memory or {}).get("prototypes", {}) if isinstance(semantic_memory, dict) else {},
        "learning_diary": diary_rows,
        "learning_counts": {"total": len(diary_rows), "by_event_type": dict(diary_counter)},
        "research_notes": _read_text_safely(research_notes_path) if research_notes_path.exists() else "",
    }


def list_available_methods() -> list[dict[str, str]]:
    return [
        {"key": "baseline", "label": "Baseline", "description": "Current best v3.5 adapter retrieval."},
        {"key": "rewrite", "label": "Rewrite", "description": "Ambiguity-aware query rewrite on top of the v3.5 baseline."},
        {"key": "rerank", "label": "Rewrite + Rerank", "description": "v3.5 baseline retrieval plus candidate semantics and semantic reranking."},
    ]


def _get_client_if_available(model: str = "gpt-4.1-mini"):
    try:
        from src.llm.client import OpenAIClient
    except Exception:
        return None
    try:
        return OpenAIClient(model=model)
    except Exception:
        return None


def _build_candidate_payload(row: dict[str, Any], rank: int, retrieval_score: float) -> dict[str, Any]:
    return {
        "video_id": row.get("video_id", ""),
        "segment_id": row.get("segment_id", ""),
        "rank": rank,
        "retrieval_score": retrieval_score,
        "video_path": row.get("video_path", ""),
        "start_sec": float(row.get("start_sec", 0.0)),
        "end_sec": float(row.get("end_sec", 0.0)),
        "duration_sec": float(row.get("duration_sec", 0.0)),
        "strategy": row.get("strategy", "video_level"),
    }


def search_demo(
    dataset_key: str,
    query_text: str,
    method: str = "baseline",
    topk: int = 5,
    gt_video_id: str | None = None,
    search_depth: int = 200,
    model_name: str = "ViT-H-14",
    pretrained: str = "laion2b_s32b_b79k",
    llm_model: str = "gpt-4.1-mini",
) -> dict[str, Any]:
    cfg = load_config()
    video_rows = _manifest_by_video(dataset_key)

    query = query_text
    initial = _search_with_current_best(dataset_key, query, topk=max(search_depth, topk, 10 if method == "rerank" else topk))
    retrieval_scores = [float(score) for _, score in initial]
    ambiguity = score_query_ambiguity(query, threshold=0.4, retrieval_scores=retrieval_scores)

    client = _get_client_if_available(model=llm_model) if method in {"rewrite", "rerank"} else None

    rewritten_query = query
    rewrite_meta: dict[str, Any] | None = None
    if method in {"rewrite", "rerank"} and client is not None:
        from src.llm.query_rewriter import rewrite_query_with_cache

        rewrite_cache = cfg.paths.project_root / "outputs" / "cache" / "rewrite"
        rewrite_meta = rewrite_query_with_cache(
            query=query,
            ambiguity=ambiguity,
            client=client,
            cache_dir=rewrite_cache,
            riskaware=True,
        )
        rewritten_query = rewrite_meta.get("rewritten_query", query)
        initial = _search_with_current_best(dataset_key, rewritten_query, topk=max(search_depth, topk, 10 if method == "rerank" else topk))
    elif method in {"rewrite", "rerank"}:
        rewrite_meta = {
            "original_query": query,
            "rewritten_query": query,
            "used_rewrite": False,
            "cache_hit": False,
            "model": None,
            "warning": "OPENAI_API_KEY not configured; rewrite/rerank fell back to baseline query.",
        }

    candidates: list[dict[str, Any]] = []
    retrieval_gt_rank: int | None = None
    for rank, (video_id, score) in enumerate(initial, start=1):
        row = video_rows.get(video_id)
        if not row:
            continue
        payload = _build_candidate_payload(row=row, rank=rank, retrieval_score=float(score))
        if gt_video_id and str(payload.get("video_id")) == str(gt_video_id) and retrieval_gt_rank is None:
            retrieval_gt_rank = rank
        candidates.append(payload)

    rerank_rows: list[dict[str, Any]] = []
    if method == "rerank" and client is not None:
        from src.llm.candidate_semantics import get_candidate_semantics_with_cache
        from src.llm.reranker import rerank_candidate_with_cache

        semantics_cache = cfg.paths.project_root / "outputs" / "cache" / "candidate_semantics"
        rerank_cache = cfg.paths.project_root / "outputs" / "cache" / "rerank"
        tmp_frame_dir = cfg.paths.project_root / "outputs" / "tmp" / "streamlit_frames"
        enriched: list[dict[str, Any]] = []
        for cand in candidates[: max(topk, 5)]:
            semantics = get_candidate_semantics_with_cache(candidate=cand, client=client, cache_dir=semantics_cache, tmp_frame_dir=tmp_frame_dir)
            cand = dict(cand)
            cand["semantic_summary"] = semantics.get("summary", "")
            cand["semantic_tags"] = semantics.get("tags", [])
            rerank = rerank_candidate_with_cache(query=query, rewritten_query=rewritten_query, candidate=cand, client=client, cache_dir=rerank_cache)
            cand["llm_score"] = rerank.get("llm_score", 50)
            cand["rerank_reason"] = rerank.get("reason", "")
            enriched.append(cand)
        enriched.sort(key=lambda row: (row.get("llm_score", 0), row.get("retrieval_score", 0.0)), reverse=True)
        rerank_rows = enriched[:topk]
    else:
        rerank_rows = candidates[:topk]

    final_gt_rank: int | None = None
    if gt_video_id:
        for idx, row in enumerate(rerank_rows, start=1):
            if str(row.get("video_id")) == str(gt_video_id):
                final_gt_rank = idx
                break

    estimated_seconds = {"baseline": 2.0, "rewrite": 8.0, "rerank": 18.0}.get(method, 3.0)
    llm_needed = method in {"rewrite", "rerank"}
    rewrite_used = bool((rewrite_meta or {}).get("used_rewrite")) if llm_needed else False

    return {
        "dataset_key": dataset_key,
        "query": query,
        "rewritten_query": rewritten_query,
        "ambiguity": ambiguity,
        "rewrite_meta": rewrite_meta,
        "results": rerank_rows,
        "index_dir": "current_best_v35_adapter",
        "method": method,
        "llm_available": client is not None,
        "llm_needed": llm_needed,
        "rewrite_used": rewrite_used,
        "gt_video_id": gt_video_id,
        "retrieval_gt_rank": retrieval_gt_rank,
        "final_gt_rank": final_gt_rank,
        "estimated_seconds": estimated_seconds,
    }


def _device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=4)
def _current_best_summary(dataset_key: str) -> dict[str, Any]:
    cfg = load_config()
    state_path = cfg.paths.project_root / "outputs" / "tables" / "analysis" / "continual_layer_state.json"
    if state_path.exists():
        state = _read_json_safely(state_path)
        if isinstance(state, dict):
            current_best = state.get("current_best", {})
            if isinstance(current_best, dict):
                summary_json = str(current_best.get("summary_json", "")).strip()
                if summary_json:
                    path = Path(summary_json)
                    if not path.is_absolute():
                        path = cfg.paths.project_root / path
                    payload = _read_json_safely(path)
                    if isinstance(payload, dict):
                        return payload
    path = cfg.paths.project_root / "outputs" / "tables" / "analysis" / "stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json"
    payload = _read_json_safely(path)
    return payload if isinstance(payload, dict) else {}


@lru_cache(maxsize=4)
def _alignment_teacher_map(dataset_key: str) -> dict[str, Any]:
    cfg = load_config()
    summary = _current_best_summary(dataset_key)
    artifacts = summary.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return {}
    alignment_path = str(artifacts.get("alignment_teacher", "")).strip()
    if not alignment_path:
        return {}
    path = Path(alignment_path)
    if not path.is_absolute():
        path = cfg.paths.project_root / path
    return {str(row.get("video_id", "")): row for row in _read_jsonl_safely(path) if row.get("video_id")}


@lru_cache(maxsize=4)
def _semantic_memory_payload(dataset_key: str) -> dict[str, Any]:
    cfg = load_config()
    summary = _current_best_summary(dataset_key)
    artifacts = summary.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return {}
    memory_path = str(artifacts.get("semantic_memory", "")).strip()
    if not memory_path:
        return {}
    path = Path(memory_path)
    if not path.is_absolute():
        path = cfg.paths.project_root / path
    return load_semantic_memory(path)


def _dataset_config(dataset_key: str) -> AdapterTrainingConfig:
    summary = _current_best_summary(dataset_key)
    techniques = summary.get("techniques", {}) if isinstance(summary.get("techniques"), dict) else {}
    artifacts = summary.get("artifacts", {}) if isinstance(summary.get("artifacts"), dict) else {}
    dataset_meta = DATASETS[dataset_key]
    return AdapterTrainingConfig(
        manifest_name=dataset_meta["manifest"],
        query_file=dataset_meta["queries"],
        pooling_mode="mean",
        model_name="ViT-H-14",
        pretrained="laion2b_s32b_b79k",
        device=_device(),
        adapter_mode=str(techniques.get("adapter_mode", "gated")),
        residual_scale=float(techniques.get("residual_scale", 0.35)),
        video_aggregation_weight=float(techniques.get("video_aggregation_weight", 0.20)),
        cross_modal_video_weight=float(techniques.get("cross_modal_video_weight", 0.10)),
        multiview_features=str(artifacts.get("multiview_features", techniques.get("multiview_features", ""))),
        multiview_weight=float(techniques.get("multiview_weight", 0.08)),
        memory_augmented_weight=float(techniques.get("memory_augmented_weight", 0.08)),
        alignment_teacher_weight=float(techniques.get("alignment_teacher_weight", 0.08)),
    )


@lru_cache(maxsize=4)
def _retrieval_dataset(dataset_key: str) -> RetrievalLearningDataset:
    return RetrievalLearningDataset.build(_dataset_config(dataset_key))


@lru_cache(maxsize=4)
def _adapter_model(dataset_key: str) -> TextResidualAdapter:
    cfg = load_config()
    summary = _current_best_summary(dataset_key)
    artifacts = summary.get("artifacts", {}) if isinstance(summary.get("artifacts"), dict) else {}
    checkpoint_path = str(artifacts.get("checkpoint", "")).strip()
    if not checkpoint_path:
        raise FileNotFoundError("Current best checkpoint is missing.")
    path = Path(checkpoint_path)
    if not path.is_absolute():
        path = cfg.paths.project_root / path
    payload = torch.load(path, map_location=_device())
    dataset = _retrieval_dataset(dataset_key)
    adapter = TextResidualAdapter(
        dim=int(dataset.video_matrix.shape[1]),
        residual_scale=dataset.config.residual_scale,
        mode=dataset.config.adapter_mode,
        video_aggregation_weight=dataset.config.video_aggregation_weight,
    ).to(dataset.config.device if torch.cuda.is_available() else "cpu")
    adapter.load_state_dict(payload["state_dict"], strict=False)
    adapter.eval()
    return adapter


@lru_cache(maxsize=4)
def _video_tensors(dataset_key: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
    dataset = _retrieval_dataset(dataset_key)
    device = dataset.config.device if torch.cuda.is_available() else "cpu"
    video_tensor = torch.tensor(dataset.video_matrix, dtype=torch.float32, device=device)
    video_max_tensor = torch.tensor(dataset.video_max_matrix, dtype=torch.float32, device=device)
    video_multiview = None
    if dataset.video_multiview_matrix is not None:
        video_multiview = torch.tensor(dataset.video_multiview_matrix, dtype=torch.float32, device=device)
    return video_tensor, video_max_tensor, video_multiview


def _search_with_current_best(
    dataset_key: str,
    query_text: str,
    topk: int,
) -> list[tuple[str, float]]:
    dataset = _retrieval_dataset(dataset_key)
    adapter = _adapter_model(dataset_key)
    device = dataset.config.device if torch.cuda.is_available() else "cpu"
    query_vec = encode_text(dataset.clip_bundle, query_text).astype(np.float32)
    query_tensor = torch.tensor(query_vec[None, :], dtype=torch.float32, device=device)
    query_tensor = adapter(query_tensor)
    video_tensor, video_max_tensor, video_multiview = _video_tensors(dataset_key)
    scores = adapter.score_video(
        query_tensor,
        video_tensor,
        video_max_tensor,
        cross_modal_video_weight=dataset.config.cross_modal_video_weight,
    )
    if dataset.config.multiview_weight > 0 and video_multiview is not None:
        mv_scores = adapter.score_multiview(query_tensor, video_multiview)
        if mv_scores is not None:
            scores = scores + dataset.config.multiview_weight * mv_scores
    semantic_memory = _semantic_memory_payload(dataset_key)
    if semantic_memory and dataset.config.memory_augmented_weight > 0:
        bonus = _memory_augmented_bonus(query_text, dataset.video_ids, semantic_memory)
        if np.any(bonus):
            scores = scores + dataset.config.memory_augmented_weight * torch.tensor(bonus, dtype=torch.float32, device=device).unsqueeze(0)
    alignment_teacher = _alignment_teacher_map(dataset_key)
    if alignment_teacher and dataset.config.alignment_teacher_weight > 0:
        bonus = _alignment_bonus(query_text, dataset.video_ids, alignment_teacher)
        if np.any(bonus):
            scores = scores + dataset.config.alignment_teacher_weight * torch.tensor(bonus, dtype=torch.float32, device=device).unsqueeze(0)
    row_scores = scores.squeeze(0).detach().cpu().numpy()
    ordering = np.argsort(-row_scores)[:topk]
    return [(dataset.video_ids[int(idx)], float(row_scores[int(idx)])) for idx in ordering]
