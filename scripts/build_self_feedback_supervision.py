from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.teacher_supervision import (  # noqa: E402
    TeacherSupervisionEntry,
    TeacherTarget,
    write_teacher_supervision,
)
from src.learning.text_adapter import (  # noqa: E402
    AdapterTrainingConfig,
    RetrievalLearningDataset,
    TextResidualAdapter,
)
from src.llm.semantic_memory import (  # noqa: E402
    derive_constraint_tags,
    extract_query_tokens,
    extract_structured_prototypes,
)
from src.utils.research_log import append_research_log  # noqa: E402


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_alignment_teacher(path_text: str) -> dict[str, Any]:
    if not path_text.strip():
        return {}
    rows = _read_jsonl(_resolve_path(path_text))
    return {str(row.get("video_id", "")): row for row in rows if row.get("video_id")}


def _alignment_terms(payload: dict[str, Any]) -> set[str]:
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


def _alignment_bonus(query: str, video_ids: list[str], alignment_teacher: dict[str, Any]) -> np.ndarray:
    if not alignment_teacher:
        return np.zeros(len(video_ids), dtype=np.float32)
    structured = extract_structured_prototypes(query)
    query_terms = set(extract_query_tokens(query))
    for values in structured.values():
        query_terms.update(values)
    if not query_terms:
        return np.zeros(len(video_ids), dtype=np.float32)

    scores: list[float] = []
    for video_id in video_ids:
        terms = _alignment_terms(alignment_teacher.get(video_id, {}))
        if not terms:
            scores.append(0.0)
            continue
        overlap = len(query_terms.intersection(terms))
        scores.append(float(overlap) / max(1, min(len(query_terms), len(terms))))
    return np.asarray(scores, dtype=np.float32)


def _component_multiview_scores(
    *,
    query: str,
    video_ids: list[str],
    video_id_to_index: dict[str, int],
    video_multiview: torch.Tensor | None,
    clip_bundle: Any,
    device: str,
) -> np.ndarray:
    if video_multiview is None:
        return np.zeros(len(video_ids), dtype=np.float32)
    structured = extract_structured_prototypes(query)
    prompts: list[str] = []
    templates = {
        "action": "a video moment showing the action of {term}",
        "object": "a video frame containing {term}",
        "scene": "a video scene in or around {term}",
        "relation": "a video frame showing the relation {term}",
    }
    for group_name, values in structured.items():
        template = templates.get(group_name, "a video frame about {term}")
        for value in values[:3]:
            value = str(value).strip().lower()
            if value:
                prompts.append(template.format(term=value))
    if not prompts:
        return np.zeros(len(video_ids), dtype=np.float32)

    from src.features.clip_encoder import encode_text

    feats = [encode_text(clip_bundle, prompt) for prompt in prompts[:8]]
    comp = np.stack(feats, axis=0).astype(np.float32)
    comp = comp / (np.linalg.norm(comp, axis=-1, keepdims=True) + 1e-12)
    comp_tensor = torch.tensor(comp, dtype=torch.float32, device=device)
    indices = [video_id_to_index[video_id] for video_id in video_ids if video_id in video_id_to_index]
    if not indices:
        return np.zeros(len(video_ids), dtype=np.float32)
    views = video_multiview[indices]
    raw_scores = torch.einsum("cd,nvd->cnv", comp_tensor, views)
    scores = raw_scores.max(dim=-1).values.mean(dim=0).detach().cpu().numpy()
    lookup = {
        video_id: float(score)
        for video_id, score in zip([video_id for video_id in video_ids if video_id in video_id_to_index], scores)
    }
    return np.asarray([lookup.get(video_id, 0.0) for video_id in video_ids], dtype=np.float32)


def _load_adapter(
    checkpoint_path: str,
    dim: int,
    config: AdapterTrainingConfig,
    device: str,
) -> TextResidualAdapter | None:
    if not checkpoint_path.strip():
        return None
    path = _resolve_path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    payload = torch.load(path, map_location=device)
    adapter = TextResidualAdapter(
        dim=dim,
        residual_scale=config.residual_scale,
        mode=config.adapter_mode,
        video_aggregation_weight=config.video_aggregation_weight,
    ).to(device)
    adapter.load_state_dict(payload["state_dict"])
    adapter.eval()
    return adapter


def _feedback_target_score(position: int, topk: int) -> float:
    if position == 0:
        return 1.0
    return float(max(0.05, 0.55 * (1.0 - position / max(topk, 1))))


def _query_error_types(query: str) -> list[str]:
    structured = extract_structured_prototypes(query)
    tokens = set(extract_query_tokens(query))
    tags: list[str] = []
    if structured.get("object"):
        tags.append("object")
    if structured.get("action"):
        tags.append("action")
    if structured.get("relation"):
        tags.append("relation")
    if tokens.intersection({"boy", "girl", "man", "woman", "child", "kid", "baby"}):
        tags.append("person_attribute")
    if structured.get("scene"):
        tags.append("scene")
    return tags or ["other"]


def _pairwise_margin_and_weight(query: str, position: int) -> tuple[float, float]:
    tags = set(_query_error_types(query))
    margin = 0.035
    weight = 1.0
    if tags.intersection({"object", "relation", "person_attribute"}):
        margin = 0.065
        weight = 1.35
    elif "action" in tags:
        margin = 0.055
        weight = 1.2
    elif "scene" in tags:
        margin = 0.03
        weight = 0.85
    if position <= 5:
        margin += 0.01
        weight += 0.15
    return float(margin), float(weight)


def _build_entry(
    row: dict[str, Any],
    ranked_video_ids: list[str],
    ranked_scores: list[float],
    component_scores: list[float],
    gt_rank: int,
    teacher_topk: int,
) -> tuple[TeacherSupervisionEntry, dict[str, Any]]:
    gt_video_id = str(row["gt_video_id"])
    qid = row.get("qid", "")
    hard_negatives = [video_id for video_id in ranked_video_ids if video_id != gt_video_id][:teacher_topk]

    target_scores: dict[str, float] = {gt_video_id: 1.0}
    score_lookup = {video_id: score for video_id, score in zip(ranked_video_ids, ranked_scores)}
    component_lookup = {
        video_id: score for video_id, score in zip(ranked_video_ids, component_scores)
    }
    for position, video_id in enumerate(ranked_video_ids[:teacher_topk], start=1):
        if video_id == gt_video_id:
            target_scores[video_id] = 1.0
        else:
            component_bonus = max(0.0, float(component_lookup.get(video_id, 0.0))) * 0.15
            target_scores[video_id] = max(
                target_scores.get(video_id, 0.0),
                _feedback_target_score(position, teacher_topk) + component_bonus,
            )

    targets = [
        TeacherTarget(video_id=video_id, score=score)
        for video_id, score in sorted(target_scores.items(), key=lambda item: item[1], reverse=True)
    ][: teacher_topk + 1]
    metadata = {
        "feedback_mode": "self_feedback_from_retrieval_vs_gt",
        "retrieval_gt_rank": gt_rank,
        "retrieval_top1": ranked_video_ids[0] if ranked_video_ids else "",
        "retrieval_top1_is_gt": bool(ranked_video_ids and ranked_video_ids[0] == gt_video_id),
        "error_types": _query_error_types(str(row["query"])),
        "pairwise_preferences": [],
        "retrieval_scores": {
            video_id: round(float(score_lookup.get(video_id, 0.0)), 6)
            for video_id in ranked_video_ids[:teacher_topk]
        },
        "component_late_interaction_scores": {
            video_id: round(float(component_lookup.get(video_id, 0.0)), 6)
            for video_id in ranked_video_ids[:teacher_topk]
        },
    }
    for position, video_id in enumerate(ranked_video_ids[:teacher_topk], start=1):
        if video_id == gt_video_id:
            continue
        margin, weight = _pairwise_margin_and_weight(str(row["query"]), position)
        metadata["pairwise_preferences"].append(
            {
                "positive": gt_video_id,
                "negative": video_id,
                "margin": margin,
                "weight": weight,
                "error_types": metadata["error_types"],
                "reason": "error_type_aware_gt_should_rank_above_hard_negative",
            }
        )
    entry = TeacherSupervisionEntry(
        qid=qid,
        query=str(row["query"]),
        gt_video_id=gt_video_id,
        source="self_feedback_retrieval_gt",
        similarity_targets=targets,
        listwise_targets=targets,
        hard_negatives=hard_negatives,
        frame_relevance=[1.0],
        prototype_terms=extract_query_tokens(str(row["query"]))[:10],
        structured_prototypes=extract_structured_prototypes(str(row["query"])),
        constraint_tags=derive_constraint_tags(str(row["query"])),
        metadata=metadata,
    )
    memory_row = {
        "schema_version": "self_feedback_memory_v2",
        "qid": qid,
        "query": str(row["query"]),
        "gt_video_id": gt_video_id,
        "gt_rank": gt_rank,
        "top1_video_id": metadata["retrieval_top1"],
        "top1_is_gt": metadata["retrieval_top1_is_gt"],
        "hard_negatives": hard_negatives,
        "topk": [
            {
                "rank": idx + 1,
                "video_id": video_id,
                "score": round(float(score), 6),
                "component_score": round(float(component_lookup.get(video_id, 0.0)), 6),
                "is_gt": video_id == gt_video_id,
            }
            for idx, (video_id, score) in enumerate(zip(ranked_video_ids, ranked_scores))
        ],
    }
    return entry, memory_row


def build_self_feedback_supervision(
    *,
    manifest_name: str,
    query_file: str,
    max_queries: int,
    search_topk: int,
    teacher_topk: int,
    model_name: str,
    pretrained: str,
    pooling: str,
    checkpoint: str,
    multiview_features: str,
    multiview_weight: float,
    multiview_pooling: str,
    multiview_temperature: float,
    alignment_teacher_path: str,
    alignment_weight: float,
    query_batch_size: int,
    failed_only: bool,
    min_gt_rank: int,
    max_gt_rank: int,
    out_memory: str,
    out_teacher: str,
) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    config = AdapterTrainingConfig(
        manifest_name=manifest_name,
        query_file=query_file,
        pooling_mode=pooling,
        model_name=model_name,
        pretrained=pretrained,
        device=device,
        max_train_queries=max_queries,
        adapter_mode="gated",
        residual_scale=0.35,
        video_aggregation_weight=0.20,
        cross_modal_video_weight=0.10,
        multiview_features=multiview_features,
        multiview_weight=multiview_weight,
        multiview_pooling=multiview_pooling,
        multiview_temperature=multiview_temperature,
    )
    dataset = RetrievalLearningDataset.build(config)
    rows = [row for row in dataset.queries if row.get("gt_video_id") in dataset.video_id_to_index]
    query_matrix = dataset.encode_queries(rows)
    adapter = _load_adapter(checkpoint, query_matrix.shape[1], config, device)
    alignment_teacher = _load_alignment_teacher(alignment_teacher_path)

    video_tensor = torch.tensor(dataset.video_matrix, dtype=torch.float32, device=device)
    video_max_tensor = torch.tensor(dataset.video_max_matrix, dtype=torch.float32, device=device)
    video_multiview = (
        torch.tensor(dataset.video_multiview_matrix, dtype=torch.float32, device=device)
        if dataset.video_multiview_matrix is not None
        else None
    )
    score_chunks: list[np.ndarray] = []
    batch_size = max(1, query_batch_size)
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            batch_np = query_matrix[start:start + batch_size]
            query_tensor = torch.tensor(batch_np, dtype=torch.float32, device=device)
            if adapter is not None:
                query_tensor = adapter(query_tensor)
                scores_tensor = adapter.score_video(
                    query_tensor,
                    video_tensor,
                    video_max_tensor,
                    cross_modal_video_weight=config.cross_modal_video_weight,
                )
                if multiview_weight > 0 and video_multiview is not None:
                    mv_scores = adapter.score_multiview(
                        query_tensor,
                        video_multiview,
                        pooling=multiview_pooling,
                        temperature=multiview_temperature,
                    )
                    if mv_scores is not None:
                        scores_tensor = scores_tensor + multiview_weight * mv_scores
            else:
                query_tensor = F.normalize(query_tensor, dim=-1)
                scores_tensor = query_tensor @ video_tensor.T
                if multiview_weight > 0 and video_multiview is not None:
                    raw_mv_scores = torch.einsum("bd,nvd->bnv", query_tensor, video_multiview)
                    if multiview_pooling == "attention":
                        mv_weights = F.softmax(
                            raw_mv_scores / max(float(multiview_temperature), 1e-4),
                            dim=-1,
                        )
                        mv_scores = (mv_weights * raw_mv_scores).sum(dim=-1)
                    else:
                        mv_scores = raw_mv_scores.max(dim=-1).values
                    scores_tensor = scores_tensor + multiview_weight * mv_scores
            score_chunks.append(scores_tensor.detach().cpu().numpy())
            if device.startswith("cuda"):
                torch.cuda.empty_cache()

    scores = (
        np.concatenate(score_chunks, axis=0)
        if score_chunks
        else np.zeros((0, len(dataset.video_ids)), dtype=np.float32)
    )
    entries: list[TeacherSupervisionEntry] = []
    memory_rows: list[dict[str, Any]] = []
    gt_ranks: list[int] = []
    selected_gt_ranks: list[int] = []
    top1_hits = 0
    selected_rows = 0
    for row_idx, row in enumerate(tqdm(rows, desc="Build self-feedback memory", dynamic_ncols=True)):
        row_scores = scores[row_idx].copy()
        if alignment_weight > 0 and alignment_teacher:
            row_scores += alignment_weight * _alignment_bonus(row["query"], dataset.video_ids, alignment_teacher)
        ordering = np.argsort(-row_scores)
        gt_idx = dataset.video_id_to_index[str(row["gt_video_id"])]
        gt_rank = int(np.where(ordering == gt_idx)[0][0]) + 1
        gt_ranks.append(gt_rank)

        ranked = ordering[:search_topk]
        ranked_video_ids = [dataset.video_ids[int(idx)] for idx in ranked]
        ranked_scores = [float(row_scores[int(idx)]) for idx in ranked]
        component_scores = _component_multiview_scores(
            query=str(row["query"]),
            video_ids=ranked_video_ids,
            video_id_to_index=dataset.video_id_to_index,
            video_multiview=video_multiview,
            clip_bundle=dataset.clip_bundle,
            device=device,
        ).tolist()
        if ranked_video_ids and ranked_video_ids[0] == str(row["gt_video_id"]):
            top1_hits += 1

        if failed_only:
            if gt_rank <= max(min_gt_rank, 1):
                continue
            if max_gt_rank > 0 and gt_rank > max_gt_rank:
                continue

        if str(row["gt_video_id"]) not in ranked_video_ids:
            ranked_video_ids.append(str(row["gt_video_id"]))
            ranked_scores.append(float(row_scores[gt_idx]))
            gt_component = _component_multiview_scores(
                query=str(row["query"]),
                video_ids=[str(row["gt_video_id"])],
                video_id_to_index=dataset.video_id_to_index,
                video_multiview=video_multiview,
                clip_bundle=dataset.clip_bundle,
                device=device,
            )
            component_scores.append(float(gt_component[0]) if len(gt_component) else 0.0)

        entry, memory_row = _build_entry(
            row=row,
            ranked_video_ids=ranked_video_ids,
            ranked_scores=ranked_scores,
            component_scores=component_scores,
            gt_rank=gt_rank,
            teacher_topk=teacher_topk,
        )
        entries.append(entry)
        memory_rows.append(memory_row)
        selected_gt_ranks.append(gt_rank)
        selected_rows += 1

    memory_path = _resolve_path(out_memory)
    teacher_path = _resolve_path(out_teacher)
    _write_jsonl(memory_path, memory_rows)
    write_teacher_supervision(teacher_path, entries)

    summary = {
        "queries": len(rows),
        "out_memory": str(memory_path),
        "out_teacher": str(teacher_path),
        "search_topk": search_topk,
        "teacher_topk": teacher_topk,
        "checkpoint": checkpoint,
        "failed_only": failed_only,
        "min_gt_rank": min_gt_rank,
        "max_gt_rank": max_gt_rank,
        "selected_rows": selected_rows,
        "top1_is_gt_rate": round(top1_hits / max(1, len(rows)), 6),
        "gt_rank_mean": round(float(np.mean(gt_ranks)), 6) if gt_ranks else None,
        "gt_rank_median": round(float(np.median(gt_ranks)), 6) if gt_ranks else None,
        "selected_gt_rank_mean": round(float(np.mean(selected_gt_ranks)), 6) if selected_gt_ranks else None,
        "selected_gt_rank_median": round(float(np.median(selected_gt_ranks)), 6) if selected_gt_ranks else None,
        "multiview_pooling": multiview_pooling,
        "multiview_temperature": multiview_temperature,
    }
    teacher_path.with_suffix(".json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    append_research_log(
        step="continual_layer::self_feedback_supervision",
        summary=(
            "已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，"
            "把正样本与 hard negatives 写入 feedback memory 和下一轮 teacher supervision。"
        ),
        decisions=[
            f"Queries: {len(rows)}",
            f"Top1 is gt rate: {summary['top1_is_gt_rate']}",
            f"Mean gt rank: {summary['gt_rank_mean']}",
            f"Selected failed ranks: ({min_gt_rank}, {max_gt_rank if max_gt_rank > 0 else 'inf'}]",
            f"Selected rows: {selected_rows}",
            f"Selected gt rank mean: {summary['selected_gt_rank_mean']}",
            f"Memory output: {memory_path}",
            f"Teacher supervision output: {teacher_path}",
            "仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。",
        ],
        citations=["teachclip_cvpr2024", "discovla_cvpr2025", "mv_adapter_cvpr2024"],
        artifacts=[str(memory_path), str(teacher_path)],
        extra=summary,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build self-feedback supervision from retrieval results and safe_train GT."
    )
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_train_9k_safe_train_queries.jsonl")
    parser.add_argument("--max_queries", type=int, default=500)
    parser.add_argument("--search_topk", type=int, default=30)
    parser.add_argument("--teacher_topk", type=int, default=20)
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--checkpoint", type=str, default="")
    parser.add_argument("--multiview_features", type=str, default="")
    parser.add_argument("--multiview_weight", type=float, default=0.0)
    parser.add_argument("--multiview_pooling", type=str, default="max", choices=["max", "attention"])
    parser.add_argument("--multiview_temperature", type=float, default=0.07)
    parser.add_argument("--alignment_teacher", type=str, default="")
    parser.add_argument("--alignment_weight", type=float, default=0.0)
    parser.add_argument("--query_batch_size", type=int, default=8)
    parser.add_argument("--failed_only", action="store_true")
    parser.add_argument("--min_gt_rank", type=int, default=1)
    parser.add_argument("--max_gt_rank", type=int, default=0)
    parser.add_argument("--out_memory", type=str, required=True)
    parser.add_argument("--out_teacher", type=str, required=True)
    args = parser.parse_args()
    build_self_feedback_supervision(
        manifest_name=args.manifest,
        query_file=args.queries,
        max_queries=args.max_queries,
        search_topk=args.search_topk,
        teacher_topk=args.teacher_topk,
        model_name=args.model_name,
        pretrained=args.pretrained,
        pooling=args.pooling,
        checkpoint=args.checkpoint,
        multiview_features=args.multiview_features,
        multiview_weight=args.multiview_weight,
        multiview_pooling=args.multiview_pooling,
        multiview_temperature=args.multiview_temperature,
        alignment_teacher_path=args.alignment_teacher,
        alignment_weight=args.alignment_weight,
        query_batch_size=args.query_batch_size,
        failed_only=args.failed_only,
        min_gt_rank=args.min_gt_rank,
        max_gt_rank=args.max_gt_rank,
        out_memory=args.out_memory,
        out_teacher=args.out_teacher,
    )


if __name__ == "__main__":
    main()
