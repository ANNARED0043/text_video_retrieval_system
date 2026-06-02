from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an adapter checkpoint on a chosen split without training.")
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
    parser.add_argument("--alignment_teacher_weight", type=float, default=0.0)
    parser.add_argument("--multiview_features", default="")
    parser.add_argument("--multiview_weight", type=float, default=0.0)
    parser.add_argument("--multiview_pooling", default="max", choices=["max", "attention"])
    parser.add_argument("--multiview_temperature", type=float, default=0.07)
    parser.add_argument("--video_temporal_adapter_weight", type=float, default=0.0)
    parser.add_argument("--component_view_weight", type=float, default=0.0)
    parser.add_argument("--query_aware_fusion", action="store_true")
    parser.add_argument("--eval_batch_size", type=int, default=8)
    parser.add_argument("--cross_modal_video_weight", type=float, default=0.10)
    parser.add_argument("--video_aggregation_weight", type=float, default=0.20)
    parser.add_argument("--adapter_mode", default="gated")
    parser.add_argument("--residual_scale", type=float, default=0.35)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    config = AdapterTrainingConfig(
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
        alignment_teacher_weight=args.alignment_teacher_weight,
        multiview_features=args.multiview_features,
        multiview_weight=args.multiview_weight,
        multiview_pooling=args.multiview_pooling,
        multiview_temperature=args.multiview_temperature,
        video_temporal_adapter_weight=args.video_temporal_adapter_weight,
        component_view_weight=args.component_view_weight,
        query_aware_fusion=args.query_aware_fusion,
        eval_batch_size=args.eval_batch_size,
    )
    dataset = RetrievalLearningDataset.build(config)
    eval_rows = [row for row in dataset.queries if row["gt_video_id"] in dataset.video_id_to_index][: args.max_eval_queries]
    adapter = _load_checkpoint(args.checkpoint, dataset.video_matrix.shape[1], config, device)
    semantic_memory = load_semantic_memory(_resolve_path(args.semantic_memory))
    alignment_teacher = _load_alignment_teacher(args.alignment_teacher)

    baseline_metrics = evaluate_adapter(
        dataset,
        eval_rows,
        adapter=None,
        semantic_memory=None,
        alignment_teacher=None,
    )
    adapter_metrics = evaluate_adapter(
        dataset,
        eval_rows,
        adapter=adapter,
        semantic_memory=None,
        alignment_teacher=None,
    )
    system_baseline_metrics = evaluate_adapter(
        dataset,
        eval_rows,
        adapter=None,
        semantic_memory=semantic_memory,
        alignment_teacher=alignment_teacher,
    )
    system_adapter_metrics = evaluate_adapter(
        dataset,
        eval_rows,
        adapter=adapter,
        semantic_memory=semantic_memory,
        alignment_teacher=alignment_teacher,
    )

    summary = {
        "stage_label": args.stage_label,
        "time": datetime.now().isoformat(timespec="seconds"),
        "eval_manifest": args.eval_manifest,
        "eval_queries": args.eval_queries,
        "student_model_name": args.student_model_name,
        "student_pretrained": args.student_pretrained,
        "eval_rows_used": len(eval_rows),
        "artifacts": {
            "summary_json": str(_resolve_path(args.out)),
            "checkpoint": str(_resolve_path(args.checkpoint)),
            "semantic_memory": str(_resolve_path(args.semantic_memory)),
            "alignment_teacher": args.alignment_teacher,
            "alignment_teacher_weight": args.alignment_teacher_weight,
            "multiview_features": args.multiview_features,
            "multiview_weight": args.multiview_weight,
            "multiview_pooling": args.multiview_pooling,
            "video_temporal_adapter_weight": args.video_temporal_adapter_weight,
            "component_view_weight": args.component_view_weight,
            "query_aware_fusion": args.query_aware_fusion,
        },
        "methods": {
            "baseline": _public_metrics(baseline_metrics),
            "adapter": _public_metrics(adapter_metrics),
        },
        "augmented_methods": {
            "baseline": _public_metrics(system_baseline_metrics),
            "adapter": _public_metrics(system_adapter_metrics),
        },
        "best_method": "adapter" if adapter_metrics["R@1"] >= baseline_metrics["R@1"] else "baseline",
        "best_metrics": _public_metrics(adapter_metrics if adapter_metrics["R@1"] >= baseline_metrics["R@1"] else baseline_metrics),
    }

    out_path = _resolve_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["methods"], ensure_ascii=False, indent=2))
    print(f"[OK] wrote eval summary: {out_path}")


if __name__ == "__main__":
    main()
