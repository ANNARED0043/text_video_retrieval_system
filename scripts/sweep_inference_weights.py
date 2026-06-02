from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any

import torch
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_stage_experiment import _load_alignment_teacher, _public_metrics  # noqa: E402
from src.learning.text_adapter import (  # noqa: E402
    AdapterTrainingConfig,
    RetrievalLearningDataset,
    TextResidualAdapter,
    evaluate_adapter,
)
from src.llm.semantic_memory import load_semantic_memory  # noqa: E402


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _parse_float_list(text: str) -> list[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def _load_checkpoint(path_text: str, dim: int, config: AdapterTrainingConfig, device: str) -> TextResidualAdapter:
    path = _resolve_path(path_text)
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


def _score_key(row: dict[str, Any]) -> tuple[float, float, float, float]:
    metrics = row["augmented_adapter"]
    return (
        float(metrics["R@1"]),
        float(metrics["R@5"]),
        float(metrics["R@10"]),
        -float(metrics["MnR"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep inference-only augmentation weights.")
    parser.add_argument("--stage_label", required=True)
    parser.add_argument("--eval_manifest", default="msrvtt_fixed_safe_dev.jsonl")
    parser.add_argument("--eval_queries", default="msrvtt_train_9k_safe_dev_queries.jsonl")
    parser.add_argument("--pooling", default="mean")
    parser.add_argument("--student_model_name", default="ViT-H-14")
    parser.add_argument("--student_pretrained", default="laion2b_s32b_b79k")
    parser.add_argument("--max_eval_queries", type=int, default=200)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--semantic_memory", default="outputs/tables/analysis/semantic_memory.json")
    parser.add_argument("--alignment_teacher", default="")
    parser.add_argument("--multiview_features", default="")
    parser.add_argument("--alignment_weights", default="0.00,0.05,0.08,0.10,0.12")
    parser.add_argument("--multiview_weights", default="0.06,0.08,0.10,0.12")
    parser.add_argument("--component_view_weights", default="0.00,0.04,0.06,0.08")
    parser.add_argument("--multiview_pooling", default="attention", choices=["max", "attention"])
    parser.add_argument("--multiview_temperature", type=float, default=0.07)
    parser.add_argument("--video_temporal_adapter_weight", type=float, default=0.0)
    parser.add_argument("--query_aware_fusion", action="store_true")
    parser.add_argument("--eval_batch_size", type=int, default=4)
    parser.add_argument("--cross_modal_video_weight", type=float, default=0.10)
    parser.add_argument("--video_aggregation_weight", type=float, default=0.20)
    parser.add_argument("--adapter_mode", default="gated")
    parser.add_argument("--residual_scale", type=float, default=0.35)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_config = AdapterTrainingConfig(
        manifest_name=args.eval_manifest,
        query_file=args.eval_queries,
        pooling_mode=args.pooling,
        model_name=args.student_model_name,
        pretrained=args.student_pretrained,
        device=device,
        max_train_queries=args.max_eval_queries,
        adapter_mode=args.adapter_mode,
        residual_scale=args.residual_scale,
        video_aggregation_weight=args.video_aggregation_weight,
        cross_modal_video_weight=args.cross_modal_video_weight,
        multiview_features=args.multiview_features,
        multiview_pooling=args.multiview_pooling,
        multiview_temperature=args.multiview_temperature,
        video_temporal_adapter_weight=args.video_temporal_adapter_weight,
        query_aware_fusion=args.query_aware_fusion,
        eval_batch_size=args.eval_batch_size,
    )
    dataset = RetrievalLearningDataset.build(base_config)
    eval_rows = [
        row for row in dataset.queries
        if row["gt_video_id"] in dataset.video_id_to_index
    ][: args.max_eval_queries]
    adapter = _load_checkpoint(args.checkpoint, dataset.video_matrix.shape[1], base_config, device)
    semantic_memory = load_semantic_memory(_resolve_path(args.semantic_memory))
    alignment_teacher = _load_alignment_teacher(args.alignment_teacher)

    results: list[dict[str, Any]] = []
    combos = list(product(
        _parse_float_list(args.alignment_weights),
        _parse_float_list(args.multiview_weights),
        _parse_float_list(args.component_view_weights),
    ))
    for align_w, mv_w, component_w in tqdm(combos, desc="Sweep inference weights", dynamic_ncols=True):
        dataset.config.alignment_teacher_weight = align_w
        dataset.config.multiview_weight = mv_w
        dataset.config.component_view_weight = component_w
        metrics = evaluate_adapter(
            dataset,
            eval_rows,
            adapter=adapter,
            semantic_memory=semantic_memory,
            alignment_teacher=alignment_teacher,
        )
        results.append({
            "alignment_teacher_weight": align_w,
            "multiview_weight": mv_w,
            "component_view_weight": component_w,
            "augmented_adapter": _public_metrics(metrics),
        })

    best = max(results, key=_score_key) if results else {}
    summary = {
        "stage_label": args.stage_label,
        "time": datetime.now().isoformat(timespec="seconds"),
        "eval_manifest": args.eval_manifest,
        "eval_queries": args.eval_queries,
        "eval_rows_used": len(eval_rows),
        "checkpoint": str(_resolve_path(args.checkpoint)),
        "alignment_teacher": args.alignment_teacher,
        "multiview_features": args.multiview_features,
        "multiview_pooling": args.multiview_pooling,
        "video_temporal_adapter_weight": args.video_temporal_adapter_weight,
        "query_aware_fusion": args.query_aware_fusion,
        "results": results,
        "best": best,
    }
    out_path = _resolve_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"best": best}, ensure_ascii=False, indent=2))
    print(f"[OK] wrote sweep summary: {out_path}")


if __name__ == "__main__":
    main()
