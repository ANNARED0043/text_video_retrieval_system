from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.research_log import append_research_log
from src.utils.stage_status import announce_stage


def _run(cmd: list[str]) -> None:
    print("[run]", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)


def main() -> None:
    announce_stage(
        "stage1",
        note="Focus on baseline retrieval, query rewrite, and candidate rerank before heavier representation learning.",
        log_step="stage_announcement::run_stage1_light_pipeline",
    )
    parser = argparse.ArgumentParser(description="Run the leakage-safe lightweight Stage 1 top-k30 teacher + distillation + quick eval pipeline.")
    parser.add_argument("--stage_label", type=str, default="stage1_viclip_topk30_safe_dev_quick200")
    parser.add_argument("--train_manifest", type=str, default="msrvtt_fixed.jsonl")
    parser.add_argument("--train_queries", type=str, default="msrvtt_train_9k_safe_train_queries.jsonl")
    parser.add_argument("--eval_manifest", type=str, default="msrvtt_fixed_safe_dev.jsonl")
    parser.add_argument("--eval_queries", type=str, default="msrvtt_train_9k_safe_dev_queries.jsonl")
    parser.add_argument("--student_model_name", type=str, default="ViT-H-14")
    parser.add_argument("--student_pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--student_topk", type=int, default=30)
    parser.add_argument("--teacher_topk", type=int, default=10)
    parser.add_argument("--max_train_queries", type=int, default=2000)
    parser.add_argument("--max_eval_queries", type=int, default=200)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--hard_negatives", type=int, default=12)
    parser.add_argument("--prototype_weight", type=float, default=0.08)
    parser.add_argument("--similarity_teacher_weight", type=float, default=0.20)
    parser.add_argument("--frame_teacher_weight", type=float, default=0.08)
    parser.add_argument("--rerank_teacher_weight", type=float, default=0.18)
    parser.add_argument("--late_interaction_weight", type=float, default=0.15)
    parser.add_argument("--residual_scale", type=float, default=0.35)
    parser.add_argument("--adapter_mode", type=str, default="gated")
    parser.add_argument("--fuse_alphas", type=str, default="0.88,0.90,0.92")
    parser.add_argument("--teacher_out", type=str, default="outputs/tables/analysis/viclip_teacher_supervision_stage1_topk30_safe_train.jsonl")
    parser.add_argument("--stage_out", type=str, default="outputs/tables/analysis/stage1_viclip_topk30_safe_dev_quick200.json")
    parser.add_argument("--gate_out", type=str, default="outputs/tables/analysis/stage1_viclip_topk30_safe_dev_gate.json")
    parser.add_argument(
        "--reference_quick",
        type=str,
        default="outputs/tables/analysis/baseline_vith14_mean_topk200_safe_dev.json",
    )
    parser.add_argument(
        "--candidate_recall_out",
        type=str,
        default="outputs/tables/analysis/baseline_vith14_candidate_recall_top30_safe_dev.json",
    )
    args = parser.parse_args()

    append_research_log(
        step=f"run_stage1_light_pipeline::{args.stage_label}",
        summary="Launch the leakage-safe Stage 1 pipeline with a safe train/dev split and a conservative adapter.",
        decisions=[
            f"Train queries default to {args.train_queries}",
            f"Quick-gate eval defaults to {args.eval_queries}",
            f"Adapter mode defaults to {args.adapter_mode}",
        ],
        citations=[
            "viclip_iclr2024",
            "teachclip_cvpr2024",
            "discovla_cvpr2025",
        ],
        artifacts=[
            args.reference_quick,
            args.teacher_out,
            args.stage_out,
            args.gate_out,
        ],
    )

    py = sys.executable
    _run(
        [
            py,
            "-u",
            "scripts/prepare_msrvtt_safe_split.py",
        ]
    )
    _run(
        [
            py,
            "-u",
            "scripts/build_index.py",
            "--manifest",
            args.eval_manifest,
            "--features_from_manifest",
            args.train_manifest,
            "--pooling",
            args.pooling,
            "--model_name",
            args.student_model_name,
            "--pretrained",
            args.student_pretrained,
        ]
    )
    _run(
        [
            py,
            "-u",
            "scripts/eval_msrvtt.py",
            "--manifest",
            args.eval_manifest,
            "--queries",
            args.eval_queries,
            "--pooling",
            args.pooling,
            "--model_name",
            args.student_model_name,
            "--pretrained",
            args.student_pretrained,
            "--topk",
            "200",
            "--max_queries",
            str(args.max_eval_queries),
            "--out",
            args.reference_quick,
        ]
    )
    _run(
        [
            py,
            "-u",
            "scripts/eval_candidate_recall.py",
            "--manifest",
            args.eval_manifest,
            "--queries",
            args.eval_queries,
            "--pooling",
            args.pooling,
            "--model_name",
            args.student_model_name,
            "--pretrained",
            args.student_pretrained,
            "--topk",
            str(args.student_topk),
            "--out",
            args.candidate_recall_out,
        ]
    )
    _run(
        [
            py,
            "-u",
            "scripts/build_viclip_teacher_supervision.py",
            "--manifest",
            args.train_manifest,
            "--queries",
            args.train_queries,
            "--pooling",
            args.pooling,
            "--student_model_name",
            args.student_model_name,
            "--student_pretrained",
            args.student_pretrained,
            "--student_topk",
            str(args.student_topk),
            "--teacher_topk",
            str(args.teacher_topk),
            "--max_queries",
            str(args.max_train_queries),
            "--checkpoint_every",
            "250",
            "--out",
            args.teacher_out,
        ]
    )
    _run(
        [
            py,
            "-u",
            "scripts/run_stage_experiment.py",
            "--stage_label",
            args.stage_label,
            "--train_manifest",
            args.train_manifest,
            "--train_queries",
            args.train_queries,
            "--eval_manifest",
            args.eval_manifest,
            "--eval_queries",
            args.eval_queries,
            "--pooling",
            args.pooling,
            "--student_model_name",
            args.student_model_name,
            "--student_pretrained",
            args.student_pretrained,
            "--max_train_queries",
            str(args.max_train_queries),
            "--max_eval_queries",
            str(args.max_eval_queries),
            "--epochs",
            str(args.epochs),
            "--hard_negatives",
            str(args.hard_negatives),
            "--teacher_topk",
            str(args.teacher_topk),
            "--prototype_weight",
            str(args.prototype_weight),
            "--similarity_teacher_weight",
            str(args.similarity_teacher_weight),
            "--frame_teacher_weight",
            str(args.frame_teacher_weight),
            "--rerank_teacher_weight",
            str(args.rerank_teacher_weight),
            "--late_interaction_weight",
            str(args.late_interaction_weight),
            "--residual_scale",
            str(args.residual_scale),
            "--adapter_mode",
            args.adapter_mode,
            "--fuse_alphas",
            args.fuse_alphas,
            "--teacher_supervision",
            args.teacher_out,
            "--out",
            args.stage_out,
        ]
    )
    _run(
        [
            py,
            "-u",
            "scripts/check_acceptance_gate.py",
            "--candidate_quick",
            str(Path(args.stage_out).with_name(f"{Path(args.stage_out).stem}_quick_eval.json")),
            "--reference_quick",
            args.reference_quick,
            "--out",
            args.gate_out,
        ]
    )

    append_research_log(
        step=f"run_stage1_light_pipeline::gate::{args.stage_label}",
        summary="Finished the Stage 1 leakage-safe pipeline and wrote the quick-gate decision.",
        decisions=[
            f"Gate file: {args.gate_out}",
            f"Reference quick baseline: {args.reference_quick}",
        ],
        citations=[
            "fine_grained_accv2024",
        ],
        artifacts=[
            args.gate_out,
        ],
    )


if __name__ == "__main__":
    main()
