from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.research_log import append_research_log


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _run(command: list[str], *, dry_run: bool) -> int:
    print(" ".join(command))
    if dry_run:
        return 0
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    return int(completed.returncode)


def _metrics(summary: dict[str, Any]) -> dict[str, float]:
    payload = summary.get("methods", {}).get("adapter", {})
    if not payload:
        payload = summary.get("best_metrics", {})
    return {
        "R@1": float(payload.get("R@1", 0.0)),
        "R@5": float(payload.get("R@5", 0.0)),
        "R@10": float(payload.get("R@10", 0.0)),
        "MedR": float(payload.get("MedR", 1e9)),
        "MnR": float(payload.get("MnR", 1e9)),
    }


def _active_best_paths(state: dict[str, Any], fallback_summary: str) -> tuple[str, str, str, str]:
    current_best = state.get("current_best", {}) if isinstance(state.get("current_best"), dict) else {}
    summary_json = str(current_best.get("summary_json", "")).strip() or fallback_summary
    checkpoint = str(current_best.get("checkpoint", "")).strip()
    alignment_teacher = str(current_best.get("alignment_teacher", "")).strip()
    multiview_features = str(current_best.get("multiview_features", "")).strip()

    if not checkpoint:
        summary = _read_json(_resolve_path(summary_json))
        artifacts = summary.get("artifacts", {}) if isinstance(summary.get("artifacts"), dict) else {}
        checkpoint = str(artifacts.get("checkpoint", "")).strip()
        alignment_teacher = alignment_teacher or str(artifacts.get("alignment_teacher", "")).strip()
        multiview_features = multiview_features or str(artifacts.get("multiview_features", "")).strip()
    return summary_json, checkpoint, alignment_teacher, multiview_features


def _feedback_paths(out_dir: Path, round_index: int) -> tuple[Path, Path]:
    prefix = out_dir / f"round{round_index:02d}"
    return (
        prefix.with_name(f"{prefix.name}_feedback_memory.jsonl"),
        prefix.with_name(f"{prefix.name}_feedback_teacher.jsonl"),
    )


def _feedback_command(
    *,
    checkpoint: str,
    multiview_features: str,
    alignment_teacher: str,
    out_memory: Path,
    out_teacher: Path,
    args: argparse.Namespace,
) -> list[str]:
    return [
        sys.executable,
        "-u",
        "scripts/build_self_feedback_supervision.py",
        "--manifest",
        args.train_manifest,
        "--queries",
        args.train_queries,
        "--max_queries",
        str(args.max_train_queries),
        "--search_topk",
        str(args.feedback_search_topk),
        "--teacher_topk",
        str(args.feedback_teacher_topk),
        "--pooling",
        args.pooling,
        "--model_name",
        args.student_model_name,
        "--pretrained",
        args.student_pretrained,
        "--checkpoint",
        checkpoint,
        "--multiview_features",
        multiview_features,
        "--multiview_weight",
        str(args.multiview_weight),
        "--alignment_teacher",
        alignment_teacher,
        "--alignment_weight",
        str(args.alignment_teacher_weight),
        "--query_batch_size",
        str(args.query_batch_size),
        "--failed_only",
        "--min_gt_rank",
        str(args.feedback_min_gt_rank),
        "--max_gt_rank",
        str(args.feedback_max_gt_rank),
        "--out_memory",
        str(out_memory),
        "--out_teacher",
        str(out_teacher),
    ]


def _reference_eval_command(
    *,
    checkpoint: str,
    alignment_teacher: str,
    multiview_features: str,
    out_path: Path,
    args: argparse.Namespace,
) -> list[str]:
    return [
        sys.executable,
        "-u",
        "scripts/evaluate_checkpoint_adapter.py",
        "--stage_label",
        "reference_current_best_eval",
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
        "--max_eval_queries",
        str(args.max_eval_queries),
        "--checkpoint",
        checkpoint,
        "--alignment_teacher",
        alignment_teacher,
        "--multiview_features",
        multiview_features,
        "--multiview_weight",
        str(args.multiview_weight),
        "--cross_modal_video_weight",
        str(args.cross_modal_video_weight),
        "--video_aggregation_weight",
        str(args.video_aggregation_weight),
        "--out",
        str(out_path),
    ]


def _stage_command(
    *,
    stage_label: str,
    teacher_supervision: Path,
    init_checkpoint: str,
    alignment_teacher: str,
    multiview_features: str,
    out_path: Path,
    args: argparse.Namespace,
) -> list[str]:
    return [
        sys.executable,
        "-u",
        "scripts/run_stage_experiment.py",
        "--stage_label",
        stage_label,
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
        "--teacher_supervision",
        str(teacher_supervision),
        "--alignment_teacher",
        alignment_teacher,
        "--multiview_features",
        multiview_features,
        "--init_checkpoint",
        init_checkpoint,
        "--stage_key",
        "stage3",
        "--sampler_mode",
        "memory",
        "--hard_negative_mode",
        "teacher_hybrid",
        "--teacher_reliability_gating",
        "--teacher_first_candidates",
        "--acceptance_gated_memory",
        "--acceptance_use_as_filter",
        "--uncertainty_aware_temperature",
        "--teacher_listwise_topk",
        str(args.teacher_listwise_topk),
        "--teacher_max_gt_rank",
        str(args.teacher_max_gt_rank),
        "--teacher_max_uncertainty",
        str(args.teacher_max_uncertainty),
        "--teacher_min_margin",
        str(args.teacher_min_margin),
        "--acceptance_max_teacher_rank",
        str(args.teacher_max_gt_rank),
        "--acceptance_max_uncertainty",
        str(args.teacher_max_uncertainty),
        "--acceptance_alignment_weight",
        "1.0",
        "--memory_refresh_topk",
        str(args.memory_refresh_topk),
        "--memory_augmented_weight",
        str(args.memory_augmented_weight),
        "--alignment_teacher_weight",
        str(args.alignment_teacher_weight),
        "--multiview_weight",
        str(args.multiview_weight),
        "--component_alignment_weight",
        str(args.component_alignment_weight),
        "--teacher_pairwise_weight",
        str(args.teacher_pairwise_weight),
        "--cross_modal_video_weight",
        str(args.cross_modal_video_weight),
        "--structured_prototype_weight",
        str(args.structured_prototype_weight),
        "--video_aggregation_weight",
        str(args.video_aggregation_weight),
        "--out",
        str(out_path),
    ]


def _promotion_command(
    *,
    current_best: str,
    candidate: Path,
    state_out: Path,
    min_r1_gain: float,
) -> list[str]:
    return [
        sys.executable,
        "-u",
        "scripts/update_continual_layer.py",
        "--current_best",
        current_best,
        "--candidate",
        str(candidate),
        "--out",
        str(state_out),
        "--min_r1_gain",
        str(min_r1_gain),
    ]


def _write_feedback(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# Error-Driven Agent Loop Feedback",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- eval split: `{payload['eval_split']}`",
        f"- rounds: {payload['rounds_requested']}",
        f"- promoted rounds: {payload['promoted_rounds']}",
        f"- locked report summary: `{payload['locked_report_summary']}`",
        f"- final active reference summary: `{payload['final_active_summary']}`",
        "",
        "## Round Review",
        "",
    ]
    for row in payload["rounds"]:
        lines.extend(
            [
                f"### Round {row['round']}",
                f"- feedback rows: {row.get('feedback_selected_rows')}",
                f"- feedback rank band: ({row.get('feedback_min_gt_rank')}, {row.get('feedback_max_gt_rank')}]",
                f"- candidate metrics: {row.get('candidate_metrics', {})}",
                f"- reference metrics before round: {row.get('reference_metrics_before_round', {})}",
                f"- delta vs reference before round: {row.get('delta_vs_reference_before_round', {})}",
                f"- promoted: {row.get('promoted')}",
                f"- reason: {row.get('promotion_reason')}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an error-driven continual agent loop based on near-failure samples."
    )
    parser.add_argument(
        "--state_json",
        default="outputs/tables/analysis/continual_layer_state.json",
    )
    parser.add_argument(
        "--fallback_current_best",
        default="outputs/tables/analysis/stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json",
    )
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--train_manifest", default="msrvtt_fixed.jsonl")
    parser.add_argument("--train_queries", default="msrvtt_train_9k_safe_train_queries.jsonl")
    parser.add_argument("--eval_manifest", default="msrvtt_fixed_safe_dev.jsonl")
    parser.add_argument("--eval_queries", default="msrvtt_train_9k_safe_dev_queries.jsonl")
    parser.add_argument("--pooling", default="mean")
    parser.add_argument("--student_model_name", default="ViT-H-14")
    parser.add_argument("--student_pretrained", default="laion2b_s32b_b79k")
    parser.add_argument("--max_train_queries", type=int, default=500)
    parser.add_argument("--max_eval_queries", type=int, default=200)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--feedback_search_topk", type=int, default=30)
    parser.add_argument("--feedback_teacher_topk", type=int, default=20)
    parser.add_argument("--feedback_min_gt_rank", type=int, default=1)
    parser.add_argument("--feedback_max_gt_rank", type=int, default=30)
    parser.add_argument("--query_batch_size", type=int, default=4)
    parser.add_argument("--teacher_listwise_topk", type=int, default=20)
    parser.add_argument("--teacher_max_gt_rank", type=int, default=20)
    parser.add_argument("--teacher_max_uncertainty", type=float, default=0.992)
    parser.add_argument("--teacher_min_margin", type=float, default=0.003)
    parser.add_argument("--memory_refresh_topk", type=int, default=280)
    parser.add_argument("--memory_augmented_weight", type=float, default=0.075)
    parser.add_argument("--alignment_teacher_weight", type=float, default=0.085)
    parser.add_argument("--multiview_weight", type=float, default=0.085)
    parser.add_argument("--component_alignment_weight", type=float, default=0.065)
    parser.add_argument("--teacher_pairwise_weight", type=float, default=0.075)
    parser.add_argument("--cross_modal_video_weight", type=float, default=0.10)
    parser.add_argument("--structured_prototype_weight", type=float, default=0.11)
    parser.add_argument("--video_aggregation_weight", type=float, default=0.20)
    parser.add_argument("--min_r1_gain", type=float, default=0.5)
    parser.add_argument(
        "--out_dir",
        default="outputs/tables/analysis/error_driven_agent_loop",
    )
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if args.rounds < 1:
        raise ValueError("--rounds must be >= 1")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_error_driven_safe_dev"
    out_dir = _resolve_path(args.out_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    state = _read_json(_resolve_path(args.state_json))
    locked_summary_path, active_checkpoint, active_alignment_teacher, active_multiview = _active_best_paths(
        state,
        args.fallback_current_best,
    )
    if not active_checkpoint:
        raise FileNotFoundError("Active best checkpoint could not be resolved.")

    reference_summary_path = out_dir / "reference_current_best_eval.json"
    reference_command = _reference_eval_command(
        checkpoint=active_checkpoint,
        alignment_teacher=active_alignment_teacher,
        multiview_features=active_multiview,
        out_path=reference_summary_path,
        args=args,
    )
    return_code = _run(reference_command, dry_run=args.dry_run)
    if return_code != 0:
        raise RuntimeError(f"Reference evaluation failed with code {return_code}.")
    active_reference_summary_path = str(reference_summary_path)

    round_rows: list[dict[str, Any]] = []
    promoted_rounds = 0

    for round_index in range(1, args.rounds + 1):
        feedback_memory_path, feedback_teacher_path = _feedback_paths(out_dir, round_index)
        feedback_command = _feedback_command(
            checkpoint=active_checkpoint,
            multiview_features=active_multiview,
            alignment_teacher=active_alignment_teacher,
            out_memory=feedback_memory_path,
            out_teacher=feedback_teacher_path,
            args=args,
        )
        return_code = _run(feedback_command, dry_run=args.dry_run)
        if return_code != 0:
            raise RuntimeError(f"Feedback supervision failed in round {round_index} with code {return_code}.")

        feedback_summary = _read_json(feedback_teacher_path.with_suffix(".json"))
        if not feedback_summary:
            feedback_summary = {
                "selected_rows": None,
                "min_gt_rank": args.feedback_min_gt_rank,
                "max_gt_rank": args.feedback_max_gt_rank,
            }

        stage_summary_path = out_dir / f"round{round_index:02d}_summary.json"
        stage_command = _stage_command(
            stage_label=f"stage3_error_driven_round{round_index:02d}",
            teacher_supervision=feedback_teacher_path,
            init_checkpoint=active_checkpoint,
            alignment_teacher=active_alignment_teacher,
            multiview_features=active_multiview,
            out_path=stage_summary_path,
            args=args,
        )
        return_code = _run(stage_command, dry_run=args.dry_run)
        if return_code != 0:
            raise RuntimeError(f"Stage experiment failed in round {round_index} with code {return_code}.")

        reference_summary = _read_json(_resolve_path(active_reference_summary_path))
        candidate_summary = _read_json(stage_summary_path) if not args.dry_run else {}
        reference_metrics = _metrics(reference_summary)
        candidate_metrics = _metrics(candidate_summary) if candidate_summary else {}
        delta = {
            key: round(candidate_metrics.get(key, 0.0) - reference_metrics.get(key, 0.0), 6)
            for key in ("R@1", "R@5", "R@10")
        } if candidate_metrics else {}

        state_out = out_dir / f"round{round_index:02d}_continual_state.json"
        promotion_command = _promotion_command(
            current_best=active_reference_summary_path,
            candidate=stage_summary_path,
            state_out=state_out,
            min_r1_gain=args.min_r1_gain,
        )
        return_code = _run(promotion_command, dry_run=args.dry_run)
        if return_code != 0:
            raise RuntimeError(f"Promotion failed in round {round_index} with code {return_code}.")

        promotion_state = _read_json(state_out) if not args.dry_run else {}
        review = promotion_state.get("candidate_review", {}) if isinstance(promotion_state.get("candidate_review"), dict) else {}
        promoted = bool(review.get("promoted", False))
        if promoted:
            promoted_rounds += 1
            current_best = promotion_state.get("current_best", {}) if isinstance(promotion_state.get("current_best"), dict) else {}
            active_reference_summary_path = str(current_best.get("summary_json", active_reference_summary_path))
            active_checkpoint = str(current_best.get("checkpoint", active_checkpoint))
            active_alignment_teacher = str(current_best.get("alignment_teacher", active_alignment_teacher))
            active_multiview = str(current_best.get("multiview_features", active_multiview))

        round_rows.append(
            {
                "round": round_index,
                "feedback_memory": str(feedback_memory_path),
                "feedback_teacher": str(feedback_teacher_path),
                "feedback_selected_rows": feedback_summary.get("selected_rows"),
                "feedback_min_gt_rank": feedback_summary.get("min_gt_rank", args.feedback_min_gt_rank),
                "feedback_max_gt_rank": feedback_summary.get("max_gt_rank", args.feedback_max_gt_rank),
                "candidate_summary": str(stage_summary_path),
                "candidate_metrics": candidate_metrics,
                "reference_summary_before_round": active_reference_summary_path,
                "reference_metrics_before_round": reference_metrics,
                "delta_vs_reference_before_round": delta,
                "promoted": promoted,
                "promotion_reason": str(review.get("reason", "")),
                "state_json": str(state_out),
            }
        )

    payload = {
        "schema_version": "error_driven_agent_loop_feedback_v2",
        "time": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "eval_split": "safe_dev",
        "rounds_requested": args.rounds,
        "promoted_rounds": promoted_rounds,
        "locked_report_summary": locked_summary_path,
        "final_active_summary": active_reference_summary_path,
        "rounds": round_rows,
    }
    feedback_path = out_dir / "loop_feedback.md"
    _write_feedback(feedback_path, payload)

    if not args.dry_run:
        append_research_log(
            step="continual_layer::error_driven_agent_loop",
            summary=(
                "已完成错误驱动 agent 学习闭环：先对当前最优 checkpoint 在 safe_dev 上建立同协议参考，"
                "再抽取 rank 2-30 的高价值失败样本，构建 feedback teacher，warm-start 训练 candidate，并通过 promotion gate 决定是否晋升。"
            ),
            decisions=[
                f"Rounds: {args.rounds}",
                f"Feedback rank band: ({args.feedback_min_gt_rank}, {args.feedback_max_gt_rank}]",
                f"Promoted rounds: {promoted_rounds}",
                f"Locked report summary: {locked_summary_path}",
                f"Safe-dev reference summary: {active_reference_summary_path}",
                "该闭环只使用 safe_train 构建反馈、safe_dev 选模、1kA 仅作锁定汇报。",
            ],
            citations=[
                "discovla_cvpr2025",
                "tokenbinder_wacv2025",
                "teachclip_cvpr2024",
                "mv_adapter_cvpr2024",
            ],
            artifacts=[str(feedback_path), str(feedback_path.with_suffix(".json"))],
            extra=payload,
        )

    print(f"[OK] error-driven agent loop: {out_dir}")
    print(f"[OK] feedback: {feedback_path}")


if __name__ == "__main__":
    main()
