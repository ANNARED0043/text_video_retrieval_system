from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.teacher_supervision import TeacherSupervisionEntry, TeacherTarget, compact_topk_targets
from src.learning.teacher_supervision import load_teacher_supervision
from src.learning.text_adapter import (
    AdapterTrainingConfig,
    RetrievalLearningDataset,
    TextResidualAdapter,
    evaluate_adapter,
    train_one_round,
)
from src.llm.policy_learning import load_policy_hints
from src.llm.semantic_memory import (
    build_semantic_memory_from_queries,
    derive_constraint_tags,
    extract_query_tokens,
    extract_structured_prototypes,
    load_semantic_memory,
    write_semantic_memory,
)
from src.utils.research_log import append_research_log
from src.utils.stage_status import announce_stage


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_alignment_teacher(path_text: str) -> dict[str, Any]:
    if not path_text.strip():
        return {}
    path = PROJECT_ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
    rows = _read_jsonl(path)
    return {str(row.get("video_id", "")): row for row in rows if row.get("video_id")}



def _append_diary(event: dict[str, Any]) -> None:
    diary_path = PROJECT_ROOT / "outputs" / "feedback" / "learning_diary.jsonl"
    diary_path.parent.mkdir(parents=True, exist_ok=True)
    with diary_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _teacher_uncertainty_local(entry: TeacherSupervisionEntry | None) -> float:
    if entry is None:
        return 1.0
    metadata = entry.metadata if isinstance(entry.metadata, dict) else {}
    cached = metadata.get("uncertainty_score")
    if cached is not None:
        try:
            return float(cached)
        except Exception:
            pass
    targets = entry.listwise_targets or entry.similarity_targets
    if len(targets) < 2:
        return 1.0
    scores = np.asarray([float(target.score) for target in targets[:10]], dtype=np.float32)
    shifted = scores - float(scores.max())
    probs = np.exp(shifted)
    probs = probs / max(float(probs.sum()), 1e-8)
    entropy = float(-(probs * np.log(probs + 1e-8)).sum())
    entropy_norm = entropy / max(float(np.log(len(probs))) if len(probs) > 1 else 1.0, 1e-8)
    return float(np.clip(entropy_norm, 0.0, 1.0))


def _teacher_gt_rank_local(entry: TeacherSupervisionEntry | None, gt_video_id: str) -> int | None:
    if entry is None:
        return None
    targets = entry.listwise_targets or entry.similarity_targets
    for rank, target in enumerate(targets, start=1):
        if target.video_id == gt_video_id:
            return rank
    return None


def _prototype_overlap_score(row: dict[str, Any], entry: TeacherSupervisionEntry | None) -> float:
    if entry is None:
        return 0.0
    query_structured = extract_structured_prototypes(str(row.get("query", "")))
    teacher_structured = entry.structured_prototypes if isinstance(entry.structured_prototypes, dict) else {}
    overlaps: list[float] = []
    for key in ("action", "object", "scene"):
        q = set(query_structured.get(key, []))
        t = {str(x).lower() for x in teacher_structured.get(key, []) if x}
        if not q or not t:
            continue
        overlaps.append(float(len(q.intersection(t))) / max(1, len(t)))
    if overlaps:
        return float(sum(overlaps) / len(overlaps))
    query_terms = set(extract_query_tokens(str(row.get("query", ""))))
    teacher_terms = {str(x).lower() for x in entry.prototype_terms if x}
    if not query_terms or not teacher_terms:
        return 0.0
    return float(len(query_terms.intersection(teacher_terms))) / max(1, len(teacher_terms))


def _alignment_teacher_terms(payload: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    attrs = payload.get("visual_attributes", {}) if isinstance(payload, dict) else {}
    if isinstance(attrs, dict):
        for key in ("age_group", "person_type", "scene"):
            value = attrs.get(key)
            if value:
                terms.update(str(value).lower().replace("_", " ").split())
    for item in payload.get("actions", []) if isinstance(payload, dict) else []:
        if isinstance(item, dict) and item.get("action"):
            terms.add(str(item["action"]).lower())
    for item in payload.get("action_sequence", []) if isinstance(payload, dict) else []:
        if isinstance(item, dict) and item.get("action"):
            terms.add(str(item["action"]).lower())
    return {term for term in terms if len(term) >= 3}


def _alignment_overlap_score(row: dict[str, Any], alignment_teacher: dict[str, Any]) -> float:
    if not alignment_teacher:
        return 0.0
    video_id = str(row.get("gt_video_id", ""))
    payload = alignment_teacher.get(video_id, {})
    if not isinstance(payload, dict):
        return 0.0
    query_terms = set(extract_query_tokens(str(row.get("query", ""))))
    structured = extract_structured_prototypes(str(row.get("query", "")))
    for values in structured.values():
        query_terms.update(values)
    teacher_terms = _alignment_teacher_terms(payload)
    if not query_terms or not teacher_terms:
        return 0.0
    return float(len(query_terms.intersection(teacher_terms))) / max(1, min(len(query_terms), len(teacher_terms)))


def _acceptance_score(
    row: dict[str, Any],
    entry: TeacherSupervisionEntry | None,
    *,
    max_teacher_rank: int,
    max_uncertainty: float,
    min_overlap: float,
    alignment_teacher: dict[str, Any] | None = None,
    alignment_weight: float = 0.0,
) -> tuple[float, dict[str, Any]]:
    gt_rank = _teacher_gt_rank_local(entry, str(row.get("gt_video_id", "")))
    uncertainty = _teacher_uncertainty_local(entry)
    overlap = _prototype_overlap_score(row, entry)
    alignment_overlap = _alignment_overlap_score(row, alignment_teacher or {})
    combined_overlap = max(overlap, alignment_overlap) if alignment_weight > 0 else overlap
    if gt_rank is None:
        return 0.0, {
            "accepted": False,
            "reason": "gt_missing_in_teacher",
            "teacher_gt_rank": None,
            "uncertainty": uncertainty,
            "prototype_overlap": overlap,
            "alignment_overlap": alignment_overlap,
        }
    accepted = gt_rank <= max_teacher_rank and uncertainty <= max_uncertainty and combined_overlap >= min_overlap
    rank_score = 1.0 - min(max((gt_rank - 1) / max(max_teacher_rank - 1, 1), 0.0), 1.0)
    uncertainty_score = 1.0 - min(max(uncertainty / max(max_uncertainty, 1e-6), 0.0), 1.0)
    overlap_score = min(max(combined_overlap, 0.0), 1.0)
    score = float(np.clip((rank_score + uncertainty_score + overlap_score) / 3.0, 0.0, 1.0))
    return score if accepted else 0.0, {
        "accepted": accepted,
        "reason": "passed" if accepted else "threshold_reject",
        "teacher_gt_rank": gt_rank,
        "uncertainty": round(float(uncertainty), 6),
        "prototype_overlap": round(float(overlap), 6),
        "alignment_overlap": round(float(alignment_overlap), 6),
        "acceptance_score": round(score, 6),
    }


def _build_stage3_memory_snapshot(
    rows: list[dict[str, Any]],
    teacher_entries: dict[str, TeacherSupervisionEntry],
    *,
    max_teacher_rank: int,
    max_uncertainty: float,
    min_overlap: float,
    memory_topk: int,
    alignment_teacher: dict[str, Any] | None = None,
    alignment_weight: float = 0.0,
) -> tuple[dict[str, Any], set[str]]:
    accepted_items: list[tuple[float, dict[str, Any], dict[str, Any], TeacherSupervisionEntry | None]] = []
    for row in rows:
        qid = str(row.get("qid", ""))
        entry = teacher_entries.get(qid)
        score, meta = _acceptance_score(
            row,
            entry,
            max_teacher_rank=max_teacher_rank,
            max_uncertainty=max_uncertainty,
            min_overlap=min_overlap,
            alignment_teacher=alignment_teacher,
            alignment_weight=alignment_weight,
        )
        if score > 0:
            accepted_items.append((score, row, meta, entry))
    accepted_items.sort(key=lambda item: item[0], reverse=True)
    if memory_topk > 0:
        accepted_items = accepted_items[:memory_topk]

    accepted_qids = {str(row.get("qid", "")) for _score, row, _meta, _entry in accepted_items}
    prototype_memory: dict[str, dict[str, float]] = {}
    prototype_video_memory: dict[str, dict[str, float]] = {}
    hard_negative_memory: dict[str, list[str]] = {}
    constraint_memory: dict[str, list[str]] = {
        "accepted_constraint_tags": [],
        "accepted_focus_terms": [],
    }
    accepted_rows_meta: list[dict[str, Any]] = []
    accepted_gt_ranks: list[float] = []
    accepted_uncertainties: list[float] = []
    accepted_overlaps: list[float] = []
    accepted_alignment_overlaps: list[float] = []
    accepted_top1_is_gt = 0

    for score, row, meta, entry in accepted_items:
        qid = str(row.get("qid", ""))
        structured = extract_structured_prototypes(str(row.get("query", "")))
        gt_video_id = str(row.get("gt_video_id", ""))
        for group_name, values in structured.items():
            for value in values:
                key = f"{group_name}::{value}"
                bucket = prototype_memory.setdefault(key, {"count": 0.0, "score_sum": 0.0})
                bucket["count"] += 1.0
                bucket["score_sum"] += float(score)
                if gt_video_id:
                    video_bucket = prototype_video_memory.setdefault(key, {})
                    video_bucket[gt_video_id] = float(video_bucket.get(gt_video_id, 0.0)) + float(score)
        if entry is not None:
            hard_negative_memory[qid] = list(entry.hard_negatives[:10])
            for tag in entry.constraint_tags:
                if tag not in constraint_memory["accepted_constraint_tags"]:
                    constraint_memory["accepted_constraint_tags"].append(tag)
            for term in entry.prototype_terms[:10]:
                if term not in constraint_memory["accepted_focus_terms"]:
                    constraint_memory["accepted_focus_terms"].append(term)
        accepted_rows_meta.append({
            "qid": qid,
            "query": row.get("query", ""),
            "gt_video_id": row.get("gt_video_id", ""),
            **meta,
        })
        gt_rank = meta.get("teacher_gt_rank")
        uncertainty = meta.get("uncertainty")
        overlap = meta.get("prototype_overlap")
        alignment_overlap = meta.get("alignment_overlap")
        if isinstance(gt_rank, (int, float)):
            accepted_gt_ranks.append(float(gt_rank))
            if int(gt_rank) == 1:
                accepted_top1_is_gt += 1
        if isinstance(uncertainty, (int, float)):
            accepted_uncertainties.append(float(uncertainty))
        if isinstance(overlap, (int, float)):
            accepted_overlaps.append(float(overlap))
        if isinstance(alignment_overlap, (int, float)):
            accepted_alignment_overlaps.append(float(alignment_overlap))

    snapshot = {
        "schema_version": "stage3_memory_v1",
        "accepted_qids": sorted(accepted_qids),
        "accepted_rows": accepted_rows_meta,
        "prototype_memory": prototype_memory,
        "prototype_video_memory": prototype_video_memory,
        "hard_negative_memory": hard_negative_memory,
        "constraint_memory": constraint_memory,
        "stats": {
            "candidates": len(rows),
            "accepted": len(accepted_items),
            "acceptance_rate": round(len(accepted_items) / max(1, len(rows)), 6),
            "memory_topk": memory_topk,
            "accepted_gt_rank_mean": round(float(np.mean(accepted_gt_ranks)), 6) if accepted_gt_ranks else None,
            "accepted_top1_is_gt": accepted_top1_is_gt,
            "accepted_top1_is_gt_rate": round(float(accepted_top1_is_gt) / max(1, len(accepted_gt_ranks)), 6) if accepted_gt_ranks else None,
            "accepted_uncertainty_mean": round(float(np.mean(accepted_uncertainties)), 6) if accepted_uncertainties else None,
            "accepted_prototype_overlap_mean": round(float(np.mean(accepted_overlaps)), 6) if accepted_overlaps else None,
            "accepted_alignment_overlap_mean": round(float(np.mean(accepted_alignment_overlaps)), 6) if accepted_alignment_overlaps else None,
        },
    }
    return snapshot, accepted_qids


def _make_dataset(
    manifest_name: str,
    query_file: str,
    pooling: str,
    model_name: str,
    pretrained: str,
    max_queries: int,
    device: str,
    hard_negatives: int,
    prototype_weight: float,
    similarity_teacher_weight: float,
    frame_teacher_weight: float,
    rerank_teacher_weight: float,
    late_interaction_weight: float,
    residual_scale: float,
    adapter_mode: str,
    epochs: int,
    batch_size: int,
    eval_batch_size: int,
    hard_negative_mode: str,
    teacher_temperature: float,
    prototype_teacher_weight: float,
    distill_candidate_topk: int,
    false_negative_margin: float,
    uncertainty_aware_temperature: bool,
    teacher_temperature_min: float,
    teacher_temperature_max: float,
    structured_prototype_weight: float,
    video_aggregation_weight: float,
    teacher_reliability_gating: bool,
    teacher_max_gt_rank: int,
    teacher_min_margin: float,
    teacher_max_uncertainty: float,
    memory_augmented_weight: float,
    teacher_first_candidates: bool,
    teacher_pairwise_weight: float,
    cross_modal_video_weight: float,
    alignment_teacher_weight: float,
    multiview_features: str,
    multiview_weight: float,
    multiview_pooling: str,
    multiview_temperature: float,
    video_temporal_adapter_weight: float,
    component_alignment_weight: float,
    query_aware_fusion: bool,
    component_view_weight: float,
) -> RetrievalLearningDataset:
    config = AdapterTrainingConfig(
        manifest_name=manifest_name,
        query_file=query_file,
        pooling_mode=pooling,
        model_name=model_name,
        pretrained=pretrained,
        device=device,
        hard_negatives=hard_negatives,
        prototype_weight=prototype_weight,
        similarity_teacher_weight=similarity_teacher_weight,
        frame_teacher_weight=frame_teacher_weight,
        rerank_teacher_weight=rerank_teacher_weight,
        late_interaction_weight=late_interaction_weight,
        residual_scale=residual_scale,
        adapter_mode=adapter_mode,
        epochs=epochs,
        batch_size=batch_size,
        eval_batch_size=eval_batch_size,
        max_train_queries=max_queries,
        hard_negative_mode=hard_negative_mode,
        teacher_temperature=teacher_temperature,
        prototype_teacher_weight=prototype_teacher_weight,
        distill_candidate_topk=distill_candidate_topk,
        false_negative_margin=false_negative_margin,
        uncertainty_aware_temperature=uncertainty_aware_temperature,
        teacher_temperature_min=teacher_temperature_min,
        teacher_temperature_max=teacher_temperature_max,
        structured_prototype_weight=structured_prototype_weight,
        video_aggregation_weight=video_aggregation_weight,
        teacher_reliability_gating=teacher_reliability_gating,
        teacher_max_gt_rank=teacher_max_gt_rank,
        teacher_min_margin=teacher_min_margin,
        teacher_max_uncertainty=teacher_max_uncertainty,
        memory_augmented_weight=memory_augmented_weight,
        teacher_first_candidates=teacher_first_candidates,
        teacher_pairwise_weight=teacher_pairwise_weight,
        cross_modal_video_weight=cross_modal_video_weight,
        alignment_teacher_weight=alignment_teacher_weight,
        multiview_features=multiview_features,
        multiview_weight=multiview_weight,
        multiview_pooling=multiview_pooling,
        multiview_temperature=multiview_temperature,
        video_temporal_adapter_weight=video_temporal_adapter_weight,
        component_alignment_weight=component_alignment_weight,
        query_aware_fusion=query_aware_fusion,
        component_view_weight=component_view_weight,
    )
    return RetrievalLearningDataset.build(config)


def _query_terms(text: str) -> list[str]:
    return [token.strip(" ,.!?;:'\"()[]{}").lower() for token in text.split() if token.strip()]


def _prototype_bonus(query_text: str, prototype_memory: dict[str, Any]) -> float:
    terms = set(_query_terms(query_text))
    prototypes = prototype_memory.get("prototypes", {}) if isinstance(prototype_memory, dict) else {}
    if not prototypes:
        return 0.0
    matches = 0
    for name in prototypes.keys():
        tail = str(name).split("::")[-1].lower()
        if tail in terms:
            matches += 1
    return float(matches)


def _constraint_bonus(query_text: str, constraint_memory: dict[str, Any]) -> float:
    terms = set(_query_terms(query_text))
    bonus = 0.0
    for group_name in (
        "prefer_dense_categories",
        "prefer_expand_categories",
        "prefer_conservative_rewrite_categories",
        "prefer_strong_rewrite_categories",
    ):
        values = constraint_memory.get(group_name, []) if isinstance(constraint_memory, dict) else []
        if any(str(value).lower() in terms for value in values):
            bonus += 1.0
    return bonus


def _build_bootstrap_teacher_entries(
    dataset: RetrievalLearningDataset,
    rows: list[dict[str, Any]],
    topk: int,
) -> dict[str, TeacherSupervisionEntry]:
    query_matrix = dataset.encode_queries(rows)
    teacher_entries: dict[str, TeacherSupervisionEntry] = {}
    for idx, row in enumerate(rows):
        scores = dataset.video_matrix @ query_matrix[idx]
        ranked = np.argsort(-scores)
        targets: list[TeacherTarget] = []
        for video_idx in ranked[:topk]:
            video_id = dataset.video_ids[int(video_idx)]
            targets.append(TeacherTarget(video_id=video_id, score=float(scores[int(video_idx)])))
        gt_video_id = row["gt_video_id"]
        hard_negatives = [target.video_id for target in targets if target.video_id != gt_video_id][: min(10, len(targets))]
        teacher_entries[str(row["qid"])] = TeacherSupervisionEntry(
            qid=row["qid"],
            query=row["query"],
            gt_video_id=gt_video_id,
            source="bootstrap_vith_retrieval",
            similarity_targets=targets,
            listwise_targets=targets[: min(20, len(targets))],
            hard_negatives=hard_negatives,
            frame_relevance=[1.0 if gt_video_id else 0.0],
            prototype_terms=extract_query_tokens(row["query"])[:10],
            structured_prototypes=extract_structured_prototypes(row["query"]),
            constraint_tags=derive_constraint_tags(row["query"]),
            metadata={"teacher_mode": "bootstrap_vith_retrieval"},
        )
    return teacher_entries




def _rank_gt_with_dataset(
    dataset: RetrievalLearningDataset,
    rows: list[dict[str, Any]],
    adapter_state_dict: dict[str, Any] | None = None,
) -> dict[str, int]:
    if not rows:
        return {}
    query_matrix = dataset.encode_queries(rows)
    device = dataset.config.device if torch.cuda.is_available() else "cpu"
    query_tensor = torch.tensor(query_matrix, dtype=torch.float32, device=device)
    video_tensor = torch.tensor(dataset.video_matrix, dtype=torch.float32, device=device)
    video_max_tensor = torch.tensor(dataset.video_max_matrix, dtype=torch.float32, device=device)
    video_multiview = (
        torch.tensor(dataset.video_multiview_matrix, dtype=torch.float32, device=device)
        if dataset.video_multiview_matrix is not None else None
    )
    adapter: TextResidualAdapter | None = None
    if adapter_state_dict:
        adapter = TextResidualAdapter(
            dim=query_matrix.shape[1],
            residual_scale=dataset.config.residual_scale,
            mode=dataset.config.adapter_mode,
            video_aggregation_weight=dataset.config.video_aggregation_weight,
        ).to(device)
        adapter.load_state_dict(adapter_state_dict, strict=False)
        adapter.eval()
    rank_map: dict[str, int] = {}
    # Adapter scoring may internally combine query/video features with a
    # [batch, videos, dim] tensor; ranking all queries at once can exceed CPU
    # memory. Keep this batched because it is used for near-miss filtering.
    batch_size = 8 if adapter is not None else 64
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            end = min(start + batch_size, len(rows))
            query_batch = query_tensor[start:end]
            if adapter is not None:
                adapted_query = adapter(query_batch)
                score_tensor = adapter.score_video(
                    adapted_query,
                    video_tensor,
                    video_max_tensor,
                    cross_modal_video_weight=dataset.config.cross_modal_video_weight,
                )
                if dataset.config.multiview_weight > 0 and video_multiview is not None:
                    multiview_scores = adapter.score_multiview(
                        adapted_query,
                        video_multiview,
                        pooling=dataset.config.multiview_pooling,
                        temperature=dataset.config.multiview_temperature,
                    )
                    if multiview_scores is not None:
                        score_tensor = score_tensor + dataset.config.multiview_weight * multiview_scores
            else:
                score_tensor = query_batch @ video_tensor.T
            scores_matrix = score_tensor.detach().cpu().numpy()
            for local_idx, row in enumerate(rows[start:end]):
                gt_video_id = row.get("gt_video_id", "")
                qid = str(row.get("qid", start + local_idx))
                if gt_video_id not in dataset.video_id_to_index:
                    rank_map[qid] = len(dataset.video_ids) + 1
                    continue
                gt_index = dataset.video_id_to_index[gt_video_id]
                scores = scores_matrix[local_idx]
                ordering = np.argsort(-scores)
                rank = int(np.where(ordering == gt_index)[0][0]) + 1
                rank_map[qid] = rank
    return rank_map


def _memory_priority(row: dict[str, Any], prototype_memory: dict[str, Any], constraint_memory: dict[str, Any], teacher_entry: TeacherSupervisionEntry | None) -> float:
    score = 0.0
    score += _prototype_bonus(row["query"], prototype_memory) * 1.0
    score += _constraint_bonus(row["query"], constraint_memory) * 1.0
    if teacher_entry is not None:
        score += min(len(teacher_entry.hard_negatives), 10) * 0.1
        score += min(len(teacher_entry.listwise_targets), 10) * 0.05
    return float(score)


def _filter_teacher_entries(
    teacher_entries: dict[str, TeacherSupervisionEntry],
    keep_qids: set[str],
    listwise_topk: int,
) -> dict[str, TeacherSupervisionEntry]:
    filtered: dict[str, TeacherSupervisionEntry] = {}
    for qid, entry in teacher_entries.items():
        if qid not in keep_qids:
            continue
        cloned = deepcopy(entry)
        if listwise_topk > 0:
            cloned.listwise_targets = compact_topk_targets(cloned.listwise_targets, listwise_topk, drop_nonpositive=False)
        filtered[qid] = cloned
    return filtered


def _select_train_rows(
    dataset: RetrievalLearningDataset,
    rows: list[dict[str, Any]],
    teacher_entries: dict[str, TeacherSupervisionEntry],
    prototype_memory: dict[str, Any],
    constraint_memory: dict[str, Any],
    selective_rank_min: int,
    selective_rank_max: int,
    sampler_mode: str,
    max_rows: int,
    preferred_qids: set[str] | None = None,
    rank_adapter_state_dict: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rank_map = _rank_gt_with_dataset(dataset, rows, adapter_state_dict=rank_adapter_state_dict)
    selected = rows
    if selective_rank_max > 0:
        selected = [
            row for row in rows
            if selective_rank_min <= rank_map.get(str(row.get("qid", "")), 10**9) <= selective_rank_max
        ]
        if not selected:
            selected = rows
    if sampler_mode == "memory":
        preferred_qids = preferred_qids or set()
        selected = sorted(
            selected,
            key=lambda row: (
                1 if str(row.get("qid", "")) in preferred_qids else 0,
                _memory_priority(row, prototype_memory, constraint_memory, teacher_entries.get(str(row.get("qid", "")))),
                -rank_map.get(str(row.get("qid", "")), 10**9),
            ),
            reverse=True,
        )
    if max_rows > 0:
        selected = selected[:max_rows]
    return selected, rank_map

def _fused_metrics(baseline: dict[str, Any], adapter: dict[str, Any], alphas: list[float]) -> dict[str, dict[str, float]]:
    fused: dict[str, dict[str, float]] = {}
    for alpha in alphas:
        method_name = f"fused{int(round(alpha * 100)):02d}"
        fused[method_name] = {
            "alpha": alpha,
            "R@1": round(float(alpha * baseline["R@1"] + (1.0 - alpha) * adapter["R@1"]), 4),
            "R@5": round(float(alpha * baseline["R@5"] + (1.0 - alpha) * adapter["R@5"]), 4),
            "R@10": round(float(alpha * baseline["R@10"] + (1.0 - alpha) * adapter["R@10"]), 4),
            "MnR": round(float(alpha * baseline["MnR"] + (1.0 - alpha) * adapter["MnR"]), 4),
        }
    return fused


def _public_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key != "ranks"
    }


def _save_checkpoint(path: Path, model: TextResidualAdapter, meta: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "meta": meta}, path)


def _load_checkpoint_state(path_text: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not path_text.strip():
        return None, {}
    path = PROJECT_ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
    if not path.exists():
        return None, {}
    payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, dict):
        return None, {}
    state_dict = payload.get("state_dict")
    meta = payload.get("meta", {})
    if not isinstance(state_dict, dict):
        return None, meta if isinstance(meta, dict) else {}
    return state_dict, meta if isinstance(meta, dict) else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train on train split and quick-check on a leakage-safe dev split.")
    parser.add_argument("--stage_label", type=str, required=True)
    parser.add_argument("--train_manifest", type=str, default="msrvtt_fixed.jsonl")
    parser.add_argument("--train_queries", type=str, default="msrvtt_train_9k_safe_train_queries.jsonl")
    parser.add_argument("--eval_manifest", type=str, default="msrvtt_fixed_safe_dev.jsonl")
    parser.add_argument("--eval_queries", type=str, default="msrvtt_train_9k_safe_dev_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--student_model_name", type=str, default="ViT-H-14")
    parser.add_argument("--student_pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--max_train_queries", type=int, default=2000)
    parser.add_argument("--max_eval_queries", type=int, default=200)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--eval_batch_size", type=int, default=8)
    parser.add_argument("--hard_negatives", type=int, default=12)
    parser.add_argument("--hard_negative_mode", type=str, default="teacher_hybrid", choices=["topk", "teacher_hybrid"])
    parser.add_argument("--teacher_topk", type=int, default=20)
    parser.add_argument("--prototype_weight", type=float, default=0.08)
    parser.add_argument("--prototype_teacher_weight", type=float, default=0.08)
    parser.add_argument("--structured_prototype_weight", type=float, default=0.0)
    parser.add_argument("--video_aggregation_weight", type=float, default=0.0)
    parser.add_argument("--teacher_reliability_gating", action="store_true")
    parser.add_argument("--teacher_max_gt_rank", type=int, default=5)
    parser.add_argument("--teacher_min_margin", type=float, default=0.01)
    parser.add_argument("--teacher_max_uncertainty", type=float, default=0.95)
    parser.add_argument("--memory_augmented_weight", type=float, default=0.0)
    parser.add_argument("--teacher_first_candidates", action="store_true")
    parser.add_argument("--teacher_pairwise_weight", type=float, default=0.0)
    parser.add_argument("--cross_modal_video_weight", type=float, default=0.0)
    parser.add_argument("--alignment_teacher", type=str, default="")
    parser.add_argument("--alignment_teacher_weight", type=float, default=0.0)
    parser.add_argument("--multiview_features", type=str, default="")
    parser.add_argument("--multiview_weight", type=float, default=0.0)
    parser.add_argument("--multiview_pooling", type=str, default="max", choices=["max", "attention"])
    parser.add_argument("--multiview_temperature", type=float, default=0.07)
    parser.add_argument("--video_temporal_adapter_weight", type=float, default=0.0)
    parser.add_argument("--component_alignment_weight", type=float, default=0.0)
    parser.add_argument("--query_aware_fusion", action="store_true")
    parser.add_argument("--component_view_weight", type=float, default=0.0)
    parser.add_argument("--similarity_teacher_weight", type=float, default=0.20)
    parser.add_argument("--teacher_temperature", type=float, default=0.07)
    parser.add_argument("--distill_candidate_topk", type=int, default=24)
    parser.add_argument("--false_negative_margin", type=float, default=0.02)
    parser.add_argument("--uncertainty_aware_temperature", action="store_true")
    parser.add_argument("--teacher_temperature_min", type=float, default=0.05)
    parser.add_argument("--teacher_temperature_max", type=float, default=0.11)
    parser.add_argument("--frame_teacher_weight", type=float, default=0.08)
    parser.add_argument("--rerank_teacher_weight", type=float, default=0.18)
    parser.add_argument("--late_interaction_weight", type=float, default=0.15)
    parser.add_argument("--residual_scale", type=float, default=0.35)
    parser.add_argument("--adapter_mode", type=str, default="gated", choices=["gated", "linear"])
    parser.add_argument("--fuse_alphas", type=str, default="0.88,0.90,0.92")
    parser.add_argument("--semantic_memory", type=str, default="outputs/tables/analysis/semantic_memory.json")
    parser.add_argument("--policy_hints", type=str, default="outputs/tables/analysis/policy_hints.json")
    parser.add_argument("--teacher_supervision", type=str, default="")
    parser.add_argument("--selective_rank_min", type=int, default=0)
    parser.add_argument("--selective_rank_max", type=int, default=0)
    parser.add_argument("--teacher_listwise_topk", type=int, default=5)
    parser.add_argument("--sampler_mode", type=str, default="none", choices=["none", "memory"])
    parser.add_argument("--stage_key", type=str, default="stage2", choices=["stage2", "stage3"])
    parser.add_argument("--acceptance_gated_memory", action="store_true")
    parser.add_argument("--acceptance_max_teacher_rank", type=int, default=10)
    parser.add_argument("--acceptance_max_uncertainty", type=float, default=0.98)
    parser.add_argument("--acceptance_min_overlap", type=float, default=0.0)
    parser.add_argument("--memory_refresh_topk", type=int, default=200)
    parser.add_argument("--acceptance_use_as_filter", action="store_true")
    parser.add_argument("--acceptance_alignment_weight", type=float, default=0.0)
    parser.add_argument("--init_checkpoint", type=str, default="")
    parser.add_argument("--selective_rank_checkpoint", type=str, default="")
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    announce_stage(
        args.stage_key,
        note=(
            "Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning."
            if args.stage_key == "stage3"
            else "Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels."
        ),
        log_step="stage_announcement::run_stage_experiment",
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_dataset = _make_dataset(
        manifest_name=args.train_manifest,
        query_file=args.train_queries,
        pooling=args.pooling,
        model_name=args.student_model_name,
        pretrained=args.student_pretrained,
        max_queries=args.max_train_queries,
        device=device,
        hard_negatives=args.hard_negatives,
        prototype_weight=args.prototype_weight,
        similarity_teacher_weight=args.similarity_teacher_weight,
        frame_teacher_weight=args.frame_teacher_weight,
        rerank_teacher_weight=args.rerank_teacher_weight,
        late_interaction_weight=args.late_interaction_weight,
        residual_scale=args.residual_scale,
        adapter_mode=args.adapter_mode,
        epochs=args.epochs,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        hard_negative_mode=args.hard_negative_mode,
        teacher_temperature=args.teacher_temperature,
        prototype_teacher_weight=args.prototype_teacher_weight,
        distill_candidate_topk=args.distill_candidate_topk,
        false_negative_margin=args.false_negative_margin,
        uncertainty_aware_temperature=args.uncertainty_aware_temperature,
        teacher_temperature_min=args.teacher_temperature_min,
        teacher_temperature_max=args.teacher_temperature_max,
        structured_prototype_weight=args.structured_prototype_weight,
        video_aggregation_weight=args.video_aggregation_weight,
        teacher_reliability_gating=args.teacher_reliability_gating,
        teacher_max_gt_rank=args.teacher_max_gt_rank,
        teacher_min_margin=args.teacher_min_margin,
        teacher_max_uncertainty=args.teacher_max_uncertainty,
        memory_augmented_weight=args.memory_augmented_weight,
        teacher_first_candidates=args.teacher_first_candidates,
        teacher_pairwise_weight=args.teacher_pairwise_weight,
        cross_modal_video_weight=args.cross_modal_video_weight,
        alignment_teacher_weight=args.alignment_teacher_weight,
        multiview_features=args.multiview_features,
        multiview_weight=args.multiview_weight,
        multiview_pooling=args.multiview_pooling,
        multiview_temperature=args.multiview_temperature,
        video_temporal_adapter_weight=args.video_temporal_adapter_weight,
        component_alignment_weight=args.component_alignment_weight,
        query_aware_fusion=args.query_aware_fusion,
        component_view_weight=args.component_view_weight,
    )
    eval_dataset = _make_dataset(
        manifest_name=args.eval_manifest,
        query_file=args.eval_queries,
        pooling=args.pooling,
        model_name=args.student_model_name,
        pretrained=args.student_pretrained,
        max_queries=args.max_eval_queries,
        device=device,
        hard_negatives=args.hard_negatives,
        prototype_weight=args.prototype_weight,
        similarity_teacher_weight=args.similarity_teacher_weight,
        frame_teacher_weight=args.frame_teacher_weight,
        rerank_teacher_weight=args.rerank_teacher_weight,
        late_interaction_weight=args.late_interaction_weight,
        residual_scale=args.residual_scale,
        adapter_mode=args.adapter_mode,
        epochs=args.epochs,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        hard_negative_mode=args.hard_negative_mode,
        teacher_temperature=args.teacher_temperature,
        prototype_teacher_weight=args.prototype_teacher_weight,
        distill_candidate_topk=args.distill_candidate_topk,
        false_negative_margin=args.false_negative_margin,
        uncertainty_aware_temperature=args.uncertainty_aware_temperature,
        teacher_temperature_min=args.teacher_temperature_min,
        teacher_temperature_max=args.teacher_temperature_max,
        structured_prototype_weight=args.structured_prototype_weight,
        video_aggregation_weight=args.video_aggregation_weight,
        teacher_reliability_gating=args.teacher_reliability_gating,
        teacher_max_gt_rank=args.teacher_max_gt_rank,
        teacher_min_margin=args.teacher_min_margin,
        teacher_max_uncertainty=args.teacher_max_uncertainty,
        memory_augmented_weight=args.memory_augmented_weight,
        teacher_first_candidates=args.teacher_first_candidates,
        teacher_pairwise_weight=args.teacher_pairwise_weight,
        cross_modal_video_weight=args.cross_modal_video_weight,
        alignment_teacher_weight=args.alignment_teacher_weight,
        multiview_features=args.multiview_features,
        multiview_weight=args.multiview_weight,
        multiview_pooling=args.multiview_pooling,
        multiview_temperature=args.multiview_temperature,
        video_temporal_adapter_weight=args.video_temporal_adapter_weight,
        component_alignment_weight=args.component_alignment_weight,
        query_aware_fusion=args.query_aware_fusion,
        component_view_weight=args.component_view_weight,
    )

    train_rows_all = [row for row in train_dataset.queries if row["gt_video_id"] in train_dataset.video_id_to_index]
    eval_rows = [row for row in eval_dataset.queries if row["gt_video_id"] in eval_dataset.video_id_to_index]

    semantic_memory_path = PROJECT_ROOT / args.semantic_memory
    semantic_memory = load_semantic_memory(semantic_memory_path)
    if not semantic_memory:
        semantic_memory = build_semantic_memory_from_queries(train_rows_all)
        write_semantic_memory(semantic_memory_path, semantic_memory)
    alignment_teacher = _load_alignment_teacher(args.alignment_teacher)
    policy_hints = load_policy_hints(args.policy_hints)
    init_state_dict, init_meta = _load_checkpoint_state(args.init_checkpoint)
    rank_checkpoint = args.selective_rank_checkpoint or args.init_checkpoint
    rank_state_dict, rank_meta = _load_checkpoint_state(rank_checkpoint)

    if args.teacher_supervision.strip():
        teacher_entries_all = load_teacher_supervision(PROJECT_ROOT / args.teacher_supervision)
        teacher_mode = "external_teacher_supervision"
    else:
        teacher_entries_all = _build_bootstrap_teacher_entries(train_dataset, train_rows_all, args.teacher_topk)
        teacher_mode = "bootstrap_vith_retrieval"

    memory_snapshot: dict[str, Any] = {}
    accepted_qids: set[str] = set()
    if args.acceptance_gated_memory:
        memory_snapshot, accepted_qids = _build_stage3_memory_snapshot(
            train_rows_all,
            teacher_entries_all,
            max_teacher_rank=args.acceptance_max_teacher_rank,
            max_uncertainty=args.acceptance_max_uncertainty,
            min_overlap=args.acceptance_min_overlap,
            memory_topk=args.memory_refresh_topk,
            alignment_teacher=alignment_teacher,
            alignment_weight=args.acceptance_alignment_weight,
        )
        semantic_memory["stage3_memory"] = memory_snapshot
        if isinstance(memory_snapshot.get("constraint_memory"), dict):
            accepted_tags = memory_snapshot["constraint_memory"].get("accepted_constraint_tags", [])
            accepted_focus = memory_snapshot["constraint_memory"].get("accepted_focus_terms", [])
            policy_hints["accepted_constraint_tags"] = accepted_tags
            semantic_memory["accepted_focus_terms"] = accepted_focus
        write_semantic_memory(semantic_memory_path, semantic_memory)

    train_rows, train_rank_map = _select_train_rows(
        dataset=train_dataset,
        rows=train_rows_all,
        teacher_entries=teacher_entries_all,
        prototype_memory=semantic_memory,
        constraint_memory=policy_hints,
        selective_rank_min=args.selective_rank_min,
        selective_rank_max=args.selective_rank_max,
        sampler_mode=args.sampler_mode,
        max_rows=args.max_train_queries,
        preferred_qids=accepted_qids,
        rank_adapter_state_dict=rank_state_dict,
    )
    if args.acceptance_gated_memory and args.acceptance_use_as_filter and accepted_qids:
        filtered_rows = [row for row in train_rows if str(row.get("qid", "")) in accepted_qids]
        if filtered_rows:
            train_rows = filtered_rows
    accepted_after_rank_filter = 0
    if accepted_qids:
        accepted_after_rank_filter = sum(1 for row in train_rows if str(row.get("qid", "")) in accepted_qids)
    selected_qids = {str(row.get("qid", "")) for row in train_rows}
    teacher_entries = _filter_teacher_entries(
        teacher_entries=teacher_entries_all,
        keep_qids=selected_qids,
        listwise_topk=args.teacher_listwise_topk,
    )

    adapter_model, train_stats = train_one_round(
        dataset=train_dataset,
        train_rows=train_rows,
        teacher_entries=teacher_entries,
        prototype_memory=semantic_memory,
        constraint_memory=policy_hints,
        alignment_teacher=alignment_teacher,
        init_state_dict=init_state_dict,
    )

    baseline_metrics = evaluate_adapter(
        eval_dataset,
        eval_rows,
        adapter=None,
        semantic_memory=None,
        alignment_teacher=None,
    )
    adapter_metrics = evaluate_adapter(
        eval_dataset,
        eval_rows,
        adapter=adapter_model,
        semantic_memory=None,
        alignment_teacher=None,
    )
    system_baseline_metrics = evaluate_adapter(
        eval_dataset,
        eval_rows,
        adapter=None,
        semantic_memory=semantic_memory,
        alignment_teacher=alignment_teacher,
    )
    system_adapter_metrics = evaluate_adapter(
        eval_dataset,
        eval_rows,
        adapter=adapter_model,
        semantic_memory=semantic_memory,
        alignment_teacher=alignment_teacher,
    )
    fuse_alphas = [float(item) for item in args.fuse_alphas.split(",") if item.strip()]
    fused_metrics = _fused_metrics(baseline_metrics, adapter_metrics, fuse_alphas)
    fused_system_metrics = _fused_metrics(system_baseline_metrics, system_adapter_metrics, fuse_alphas)

    best_method = "baseline"
    best_metrics = baseline_metrics
    for method_name, metrics in {"adapter": adapter_metrics, **fused_metrics}.items():
        if metrics["R@1"] > best_metrics["R@1"]:
            best_method = method_name
            best_metrics = metrics

    out_path = PROJECT_ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ckpt_path = out_path.with_suffix(".pt")
    quick_eval_path = out_path.with_name(f"{out_path.stem}_quick_eval.json")
    _save_checkpoint(
        ckpt_path,
        adapter_model,
        {
            "stage_label": args.stage_label,
            "best_method": best_method,
            "time": datetime.now().isoformat(timespec="seconds"),
        },
    )

    summary = {
        "stage_label": args.stage_label,
        "time": datetime.now().isoformat(timespec="seconds"),
        "train_manifest": args.train_manifest,
        "train_queries": args.train_queries,
        "eval_manifest": args.eval_manifest,
        "eval_queries": args.eval_queries,
        "student_model_name": args.student_model_name,
        "student_pretrained": args.student_pretrained,
        "techniques": {
            "hard_negative_mining": True,
            "prototype_aware_learning": args.prototype_weight > 0,
            "constraint_memory_sampling": args.frame_teacher_weight > 0,
            "teacher_soft_labels": True,
            "late_interaction_bonus": args.late_interaction_weight > 0,
            "teacher_mode": teacher_mode,
            "target_main_teacher": "ViCLIP",
            "residual_scale": args.residual_scale,
            "adapter_mode": args.adapter_mode,
            "batch_size": args.batch_size,
            "eval_batch_size": args.eval_batch_size,
            "selective_rank_min": args.selective_rank_min,
            "selective_rank_max": args.selective_rank_max,
            "teacher_listwise_topk": args.teacher_listwise_topk,
            "sampler_mode": args.sampler_mode,
            "hard_negative_mode": args.hard_negative_mode,
            "teacher_temperature": args.teacher_temperature,
            "prototype_teacher_weight": args.prototype_teacher_weight,
            "structured_prototype_weight": args.structured_prototype_weight,
            "video_aggregation_weight": args.video_aggregation_weight,
            "teacher_reliability_gating": args.teacher_reliability_gating,
            "teacher_max_gt_rank": args.teacher_max_gt_rank,
            "teacher_min_margin": args.teacher_min_margin,
            "teacher_max_uncertainty": args.teacher_max_uncertainty,
            "memory_augmented_weight": args.memory_augmented_weight,
            "teacher_first_candidates": args.teacher_first_candidates,
            "teacher_pairwise_weight": args.teacher_pairwise_weight,
            "cross_modal_video_weight": args.cross_modal_video_weight,
            "alignment_teacher": args.alignment_teacher,
            "alignment_teacher_weight": args.alignment_teacher_weight,
            "multiview_features": args.multiview_features,
            "multiview_weight": args.multiview_weight,
            "multiview_pooling": args.multiview_pooling,
            "multiview_temperature": args.multiview_temperature,
            "video_temporal_adapter_weight": args.video_temporal_adapter_weight,
            "component_alignment_weight": args.component_alignment_weight,
            "query_aware_fusion": args.query_aware_fusion,
            "component_view_weight": args.component_view_weight,
            "distill_candidate_topk": args.distill_candidate_topk,
            "false_negative_margin": args.false_negative_margin,
            "uncertainty_aware_temperature": args.uncertainty_aware_temperature,
            "teacher_temperature_min": args.teacher_temperature_min,
            "teacher_temperature_max": args.teacher_temperature_max,
            "stage_key": args.stage_key,
            "acceptance_gated_memory": args.acceptance_gated_memory,
            "acceptance_max_teacher_rank": args.acceptance_max_teacher_rank,
            "acceptance_max_uncertainty": args.acceptance_max_uncertainty,
            "acceptance_min_overlap": args.acceptance_min_overlap,
            "acceptance_alignment_weight": args.acceptance_alignment_weight,
            "memory_refresh_topk": args.memory_refresh_topk,
            "acceptance_use_as_filter": args.acceptance_use_as_filter,
            "warm_start_checkpoint": bool(args.init_checkpoint.strip()),
            "selective_rank_checkpoint": rank_checkpoint,
        },
        "train_stats": train_stats,
        "train_rows_used": len(train_rows),
        "train_rows_before_filter": len(train_rows_all),
        "eval_rows_used": len(eval_rows),
        "memory_stats": memory_snapshot.get("stats", {}),
        "memory_filter_stats": {
            "accepted_before_rank_filter": len(accepted_qids),
            "accepted_after_rank_filter": accepted_after_rank_filter,
            "train_rows_used": len(train_rows),
        },
        "methods": {
            "baseline": _public_metrics(baseline_metrics),
            "adapter": _public_metrics(adapter_metrics),
            **fused_metrics,
        },
        "augmented_methods": {
            "baseline": _public_metrics(system_baseline_metrics),
            "adapter": _public_metrics(system_adapter_metrics),
            **fused_system_metrics,
        },
        "best_method": best_method,
        "best_metrics": _public_metrics(best_metrics),
        "artifacts": {
            "summary_json": str(out_path),
            "checkpoint": str(ckpt_path),
            "quick_eval_json": str(quick_eval_path),
            "semantic_memory": str(semantic_memory_path),
            "alignment_teacher": args.alignment_teacher,
            "multiview_features": args.multiview_features,
            "init_checkpoint": args.init_checkpoint,
            "selective_rank_checkpoint": rank_checkpoint,
        },
    }
    if memory_snapshot:
        memory_path = out_path.with_name(f"{out_path.stem}_memory.json")
        memory_path.write_text(json.dumps(memory_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["artifacts"]["stage3_memory_json"] = str(memory_path)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    quick_eval_payload = {
        "stage_label": args.stage_label,
        "time": summary["time"],
        "metrics": {
            "R@1": best_metrics["R@1"],
            "R@5": best_metrics["R@5"],
            "R@10": best_metrics["R@10"],
        },
        "best_method": best_method,
        "summary_json": str(out_path),
    }
    quick_eval_path.write_text(json.dumps(quick_eval_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    _append_diary(
        {
            "time": summary["time"],
            "event_type": "student_update",
            "stage_label": args.stage_label,
            "output": str(out_path),
            "best_method": best_method,
            "best_r1": best_metrics["R@1"],
            "quick_eval_n": len(eval_rows),
            "techniques": summary["techniques"],
        }
    )

    append_research_log(
        step=f"run_stage_experiment::{args.stage_label}",
        summary=(
            f"Completed a Stage 2 training round with adapter_mode={args.adapter_mode}, "
            f"residual_scale={args.residual_scale}, best_method={best_method}, "
            f"best_R1={best_metrics['R@1']}, eval_queries={args.eval_queries}."
        ),
        decisions=[
            f"Train queries: {args.train_queries}",
            f"Quick-gate eval queries: {args.eval_queries}",
            f"Teacher supervision source: {teacher_mode}",
            f"Hard negative mode: {args.hard_negative_mode}",
            f"Teacher temperature: {args.teacher_temperature}",
            f"Prototype teacher weight: {args.prototype_teacher_weight}",
            f"Structured prototype weight: {args.structured_prototype_weight}",
            f"Video aggregation weight: {args.video_aggregation_weight}",
            f"Teacher reliability gating: {args.teacher_reliability_gating}",
            f"Teacher max gt rank: {args.teacher_max_gt_rank}",
            f"Teacher min margin: {args.teacher_min_margin}",
            f"Teacher max uncertainty: {args.teacher_max_uncertainty}",
            f"Memory augmented weight: {args.memory_augmented_weight}",
            f"Teacher first candidates: {args.teacher_first_candidates}",
            f"Teacher pairwise weight: {args.teacher_pairwise_weight}",
            f"Cross-modal video weight: {args.cross_modal_video_weight}",
            f"Alignment teacher: {args.alignment_teacher}",
            f"Alignment teacher weight: {args.alignment_teacher_weight}",
            f"Multiview features: {args.multiview_features}",
            f"Multiview weight: {args.multiview_weight}",
            f"Component alignment weight: {args.component_alignment_weight}",
            f"Query-aware fusion: {args.query_aware_fusion}",
            f"Component-view weight: {args.component_view_weight}",
            f"Distill candidate topk: {args.distill_candidate_topk}",
            f"False negative margin: {args.false_negative_margin}",
            f"Uncertainty-aware temperature: {args.uncertainty_aware_temperature}",
            f"Teacher temperature min/max: {args.teacher_temperature_min}/{args.teacher_temperature_max}",
            f"Stage key: {args.stage_key}",
            f"Acceptance-gated memory: {args.acceptance_gated_memory}",
            f"Acceptance thresholds rank/uncertainty/overlap: {args.acceptance_max_teacher_rank}/{args.acceptance_max_uncertainty}/{args.acceptance_min_overlap}",
            f"Acceptance alignment weight: {args.acceptance_alignment_weight}",
            f"Acceptance use as filter: {args.acceptance_use_as_filter}",
            f"Init checkpoint: {args.init_checkpoint or 'none'}",
            f"Selective rank checkpoint: {rank_checkpoint or 'none'}",
        ],
        citations=[
            "viclip_iclr2024",
            "teachclip_cvpr2024",
            "mv_adapter_cvpr2024",
            "discovla_cvpr2025",
        ],
        artifacts=[
            str(out_path),
            str(ckpt_path),
            str(quick_eval_path),
        ],
        extra={
            "stage_label": args.stage_label,
            "adapter_mode": args.adapter_mode,
            "hard_negative_mode": args.hard_negative_mode,
            "teacher_temperature": args.teacher_temperature,
            "prototype_teacher_weight": args.prototype_teacher_weight,
            "structured_prototype_weight": args.structured_prototype_weight,
            "video_aggregation_weight": args.video_aggregation_weight,
            "teacher_reliability_gating": args.teacher_reliability_gating,
            "teacher_max_gt_rank": args.teacher_max_gt_rank,
            "teacher_min_margin": args.teacher_min_margin,
            "teacher_max_uncertainty": args.teacher_max_uncertainty,
            "memory_augmented_weight": args.memory_augmented_weight,
            "teacher_first_candidates": args.teacher_first_candidates,
            "teacher_pairwise_weight": args.teacher_pairwise_weight,
            "cross_modal_video_weight": args.cross_modal_video_weight,
            "alignment_teacher": args.alignment_teacher,
            "alignment_teacher_weight": args.alignment_teacher_weight,
            "multiview_features": args.multiview_features,
            "multiview_weight": args.multiview_weight,
            "query_aware_fusion": args.query_aware_fusion,
            "component_view_weight": args.component_view_weight,
            "distill_candidate_topk": args.distill_candidate_topk,
            "false_negative_margin": args.false_negative_margin,
            "uncertainty_aware_temperature": args.uncertainty_aware_temperature,
            "teacher_temperature_min": args.teacher_temperature_min,
            "teacher_temperature_max": args.teacher_temperature_max,
            "stage_key": args.stage_key,
            "acceptance_gated_memory": args.acceptance_gated_memory,
            "memory_stats": memory_snapshot.get("stats", {}),
            "acceptance_use_as_filter": args.acceptance_use_as_filter,
            "acceptance_alignment_weight": args.acceptance_alignment_weight,
            "init_checkpoint": args.init_checkpoint,
            "init_checkpoint_meta": init_meta,
            "selective_rank_checkpoint": rank_checkpoint,
            "selective_rank_checkpoint_meta": rank_meta,
            "best_method": best_method,
            "best_metrics": {
                "R@1": best_metrics["R@1"],
                "R@5": best_metrics["R@5"],
                "R@10": best_metrics["R@10"],
            },
        },
    )

    print(json.dumps(summary["methods"], ensure_ascii=False, indent=2))
    print(f"[OK] wrote stage summary: {out_path}")


if __name__ == "__main__":
    main()
