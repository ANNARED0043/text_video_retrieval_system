from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.text_adapter import AdapterTrainingConfig, RetrievalLearningDataset, TextResidualAdapter
from src.llm.semantic_memory import extract_query_tokens, extract_structured_prototypes
from src.utils.research_log import append_research_log


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
    adapter.load_state_dict(payload["state_dict"], strict=False)
    adapter.eval()
    return adapter


def _rank_bucket(rank: int) -> str:
    if rank == 1:
        return "top1"
    if rank <= 5:
        return "top2_5"
    if rank <= 10:
        return "top6_10"
    if rank <= 30:
        return "top11_30"
    return "gt_outside_top30"


def _query_failure_tags(query: str) -> list[str]:
    structured = extract_structured_prototypes(query)
    tags: list[str] = []
    if structured.get("action"):
        tags.append("action")
    if structured.get("object"):
        tags.append("object")
    if structured.get("scene"):
        tags.append("scene")
    if structured.get("relation"):
        tags.append("relation")
    if len(structured.get("action", [])) >= 2:
        tags.append("multi_action")
    tokens = set(extract_query_tokens(query))
    if tokens.intersection({"boy", "girl", "man", "woman", "child", "kid", "baby"}):
        tags.append("person_attribute")
    if tokens.intersection({"first", "then", "after", "before", "while"}):
        tags.append("temporal_order")
    return tags or ["other"]


def diagnose_retrieval_failures(
    *,
    manifest_name: str,
    query_file: str,
    max_queries: int,
    model_name: str,
    pretrained: str,
    pooling: str,
    checkpoint: str,
    multiview_features: str,
    multiview_weight: float,
    alignment_teacher_path: str,
    alignment_weight: float,
    query_batch_size: int,
    out: str,
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
        if dataset.video_multiview_matrix is not None else None
    )
    score_chunks: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(rows), max(1, query_batch_size)):
            batch_np = query_matrix[start:start + max(1, query_batch_size)]
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
                    mv_scores = adapter.score_multiview(query_tensor, video_multiview)
                    if mv_scores is not None:
                        scores_tensor = scores_tensor + multiview_weight * mv_scores
            else:
                query_tensor = F.normalize(query_tensor, dim=-1)
                scores_tensor = query_tensor @ video_tensor.T
                if multiview_weight > 0 and video_multiview is not None:
                    mv_scores = torch.einsum("bd,nvd->bnv", query_tensor, video_multiview).max(dim=-1).values
                    scores_tensor = scores_tensor + multiview_weight * mv_scores
            score_chunks.append(scores_tensor.detach().cpu().numpy())
            if device.startswith("cuda"):
                torch.cuda.empty_cache()
    scores = np.concatenate(score_chunks, axis=0) if score_chunks else np.zeros((0, len(dataset.video_ids)), dtype=np.float32)

    bucket_counter = Counter()
    failure_counter = Counter()
    success_counter = Counter()
    failure_cases: list[dict[str, Any]] = []
    for row_idx, row in enumerate(tqdm(rows, desc="Diagnose failures", dynamic_ncols=True)):
        row_scores = scores[row_idx].copy()
        if alignment_weight > 0 and alignment_teacher:
            row_scores += alignment_weight * _alignment_bonus(row["query"], dataset.video_ids, alignment_teacher)
        ordering = np.argsort(-row_scores)
        gt_idx = dataset.video_id_to_index[str(row["gt_video_id"])]
        gt_rank = int(np.where(ordering == gt_idx)[0][0]) + 1
        bucket = _rank_bucket(gt_rank)
        bucket_counter[bucket] += 1
        tags = _query_failure_tags(str(row["query"]))
        target_counter = success_counter if gt_rank == 1 else failure_counter
        for tag in tags:
            target_counter[tag] += 1
        if gt_rank > 1:
            top5 = [
                {
                    "rank": i + 1,
                    "video_id": dataset.video_ids[int(idx)],
                    "score": round(float(row_scores[int(idx)]), 6),
                }
                for i, idx in enumerate(ordering[:5])
            ]
            failure_cases.append(
                {
                    "qid": row.get("qid"),
                    "query": row.get("query"),
                    "gt_video_id": row.get("gt_video_id"),
                    "gt_rank": gt_rank,
                    "bucket": bucket,
                    "tags": tags,
                    "top5": top5,
                }
            )

    report = {
        "schema_version": "retrieval_failure_diagnosis_v1",
        "manifest": manifest_name,
        "queries": query_file,
        "checkpoint": checkpoint,
        "max_queries": len(rows),
        "rank_buckets": dict(bucket_counter),
        "failure_tag_counts": dict(failure_counter.most_common()),
        "success_tag_counts": dict(success_counter.most_common()),
        "failure_cases_top50": sorted(failure_cases, key=lambda item: item["gt_rank"], reverse=True)[:50],
    }
    out_path = _resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    append_research_log(
        step="continual_layer::failure_diagnosis",
        summary="已完成当前检索模型失败样本诊断，统计不同 rank bucket 和 query 语义类型下的错误分布。",
        decisions=[
            f"Manifest: {manifest_name}",
            f"Queries: {query_file}",
            f"Checkpoint: {checkpoint}",
            f"Top failure buckets: {dict(bucket_counter)}",
            f"Top failure tags: {dict(failure_counter.most_common(5))}",
        ],
        citations=["discovla_cvpr2025", "tokenbinder_wacv2025", "blim_iccv2025"],
        artifacts=[str(out_path)],
        extra=report,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose retrieval failure patterns for the current checkpoint.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--max_queries", type=int, default=200)
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--multiview_features", type=str, default="")
    parser.add_argument("--multiview_weight", type=float, default=0.0)
    parser.add_argument("--alignment_teacher", type=str, default="")
    parser.add_argument("--alignment_weight", type=float, default=0.0)
    parser.add_argument("--query_batch_size", type=int, default=8)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    diagnose_retrieval_failures(
        manifest_name=args.manifest,
        query_file=args.queries,
        max_queries=args.max_queries,
        model_name=args.model_name,
        pretrained=args.pretrained,
        pooling=args.pooling,
        checkpoint=args.checkpoint,
        multiview_features=args.multiview_features,
        multiview_weight=args.multiview_weight,
        alignment_teacher_path=args.alignment_teacher,
        alignment_weight=args.alignment_weight,
        query_batch_size=args.query_batch_size,
        out=args.out,
    )


if __name__ == "__main__":
    main()
