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


STRATEGIES: dict[str, dict[str, Any]] = {
    "v35_plus": {
        "description": (
            "Current-best anchored strategy. Start from the v35 50.5 R@1 setup "
            "and only explore small positive-gain perturbations around it."
        ),
        "papers": ["DiscoVLA CVPR 2025", "TokenBinder WACV 2025"],
        "candidates_per_round": 4,
        "max_train_queries": 500,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 20,
        "teacher_max_gt_rank": 20,
        "teacher_max_uncertainty": 0.995,
        "teacher_min_margin": 0.003,
        "acceptance_max_teacher_rank": 20,
        "acceptance_max_uncertainty": 0.995,
        "memory_refresh_topk": 300,
        "memory_augmented_weight": 0.08,
        "alignment_teacher_weight": 0.08,
        "multiview_weight": 0.08,
        "component_alignment_weight": 0.0,
        "teacher_pairwise_weight": 0.06,
        "cross_modal_video_weight": 0.10,
        "structured_prototype_weight": 0.10,
        "video_aggregation_weight": 0.20,
    },
    "hybrid_elite": {
        "description": (
            "DiscoVLA-style discrepancy reduction + TokenBinder-style "
            "one-to-many candidate comparison + conservative memory replay."
        ),
        "papers": ["DiscoVLA CVPR 2025", "TokenBinder WACV 2025", "MAMA 2026"],
        "candidates_per_round": 3,
        "max_train_queries": 1000,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 20,
        "teacher_max_gt_rank": 20,
        "teacher_max_uncertainty": 0.992,
        "teacher_min_margin": 0.003,
        "acceptance_max_teacher_rank": 20,
        "acceptance_max_uncertainty": 0.992,
        "memory_refresh_topk": 360,
        "memory_augmented_weight": 0.075,
        "alignment_teacher_weight": 0.085,
        "multiview_weight": 0.085,
        "component_alignment_weight": 0.065,
        "teacher_pairwise_weight": 0.065,
        "cross_modal_video_weight": 0.10,
        "structured_prototype_weight": 0.11,
        "video_aggregation_weight": 0.20,
    },
    "discovla_precision": {
        "description": (
            "Higher-quality alignment-first learning; tighter teacher/memory "
            "gate to reduce noisy pseudo supervision."
        ),
        "papers": ["DiscoVLA CVPR 2025", "TeachCLIP CVPR 2024"],
        "candidates_per_round": 2,
        "max_train_queries": 700,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 10,
        "teacher_max_gt_rank": 10,
        "teacher_max_uncertainty": 0.985,
        "teacher_min_margin": 0.004,
        "acceptance_max_teacher_rank": 10,
        "acceptance_max_uncertainty": 0.985,
        "memory_refresh_topk": 260,
        "memory_augmented_weight": 0.055,
        "alignment_teacher_weight": 0.09,
        "multiview_weight": 0.07,
        "component_alignment_weight": 0.07,
        "teacher_pairwise_weight": 0.045,
        "cross_modal_video_weight": 0.08,
        "structured_prototype_weight": 0.12,
        "video_aggregation_weight": 0.16,
    },
    "tokenbinder_margin": {
        "description": (
            "Candidate-difference learning; stronger listwise and pairwise "
            "pressure for top-1 separation."
        ),
        "papers": ["TokenBinder WACV 2025"],
        "candidates_per_round": 2,
        "max_train_queries": 900,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 15,
        "teacher_max_gt_rank": 15,
        "teacher_max_uncertainty": 0.995,
        "teacher_min_margin": 0.0025,
        "acceptance_max_teacher_rank": 15,
        "acceptance_max_uncertainty": 0.995,
        "memory_refresh_topk": 400,
        "memory_augmented_weight": 0.075,
        "alignment_teacher_weight": 0.065,
        "multiview_weight": 0.085,
        "component_alignment_weight": 0.055,
        "teacher_pairwise_weight": 0.09,
        "cross_modal_video_weight": 0.11,
        "structured_prototype_weight": 0.09,
        "video_aggregation_weight": 0.22,
    },
    "mama_replay": {
        "description": (
            "Noise-robust replay-oriented learning; broader memory with "
            "uncertainty-aware distillation."
        ),
        "papers": ["MAMA 2026", "Continual replay learning"],
        "candidates_per_round": 2,
        "max_train_queries": 1200,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 12,
        "teacher_max_gt_rank": 14,
        "teacher_max_uncertainty": 0.997,
        "teacher_min_margin": 0.002,
        "acceptance_max_teacher_rank": 14,
        "acceptance_max_uncertainty": 0.997,
        "memory_refresh_topk": 520,
        "memory_augmented_weight": 0.105,
        "alignment_teacher_weight": 0.065,
        "multiview_weight": 0.07,
        "component_alignment_weight": 0.05,
        "teacher_pairwise_weight": 0.06,
        "cross_modal_video_weight": 0.10,
        "structured_prototype_weight": 0.09,
        "video_aggregation_weight": 0.20,
    },
    "conservative": {
        "description": "Legacy conservative preset.",
        "papers": ["DiscoVLA CVPR 2025"],
        "candidates_per_round": 1,
        "max_train_queries": 500,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 10,
        "teacher_max_gt_rank": 10,
        "teacher_max_uncertainty": 0.985,
        "teacher_min_margin": 0.004,
        "acceptance_max_teacher_rank": 10,
        "acceptance_max_uncertainty": 0.985,
        "memory_refresh_topk": 220,
        "memory_augmented_weight": 0.06,
        "alignment_teacher_weight": 0.06,
        "multiview_weight": 0.06,
        "component_alignment_weight": 0.04,
        "teacher_pairwise_weight": 0.04,
        "cross_modal_video_weight": 0.08,
        "structured_prototype_weight": 0.08,
        "video_aggregation_weight": 0.16,
    },
    "balanced": {
        "description": "Legacy balanced preset.",
        "papers": ["DiscoVLA CVPR 2025", "TokenBinder WACV 2025"],
        "candidates_per_round": 1,
        "max_train_queries": 1000,
        "max_eval_queries": 200,
        "epochs": 1,
        "teacher_listwise_topk": 12,
        "teacher_max_gt_rank": 12,
        "teacher_max_uncertainty": 0.995,
        "teacher_min_margin": 0.003,
        "acceptance_max_teacher_rank": 12,
        "acceptance_max_uncertainty": 0.995,
        "memory_refresh_topk": 350,
        "memory_augmented_weight": 0.08,
        "alignment_teacher_weight": 0.08,
        "multiview_weight": 0.08,
        "component_alignment_weight": 0.06,
        "teacher_pairwise_weight": 0.06,
        "cross_modal_video_weight": 0.10,
        "structured_prototype_weight": 0.10,
        "video_aggregation_weight": 0.20,
    },
    "exploratory": {
        "description": "Legacy exploratory preset.",
        "papers": ["DiscoVLA CVPR 2025", "MAMA 2026"],
        "candidates_per_round": 1,
        "max_train_queries": 1500,
        "max_eval_queries": 300,
        "epochs": 2,
        "teacher_listwise_topk": 15,
        "teacher_max_gt_rank": 15,
        "teacher_max_uncertainty": 0.998,
        "teacher_min_margin": 0.002,
        "acceptance_max_teacher_rank": 15,
        "acceptance_max_uncertainty": 0.998,
        "memory_refresh_topk": 500,
        "memory_augmented_weight": 0.10,
        "alignment_teacher_weight": 0.10,
        "multiview_weight": 0.10,
        "component_alignment_weight": 0.08,
        "teacher_pairwise_weight": 0.08,
        "cross_modal_video_weight": 0.12,
        "structured_prototype_weight": 0.12,
        "video_aggregation_weight": 0.24,
    },
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _teacher_qid_count(path_text: str) -> int:
    if not path_text.strip():
        return 0
    path = _resolve_path(path_text)
    if not path.exists():
        return 0
    qids: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            qid = row.get("qid")
            if qid is not None:
                qids.add(str(qid))
    return len(qids)


def _checkpoint_from_summary(summary_path_text: str) -> str:
    summary = _read_json(_resolve_path(summary_path_text))
    artifacts = summary.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return ""
    checkpoint = str(artifacts.get("checkpoint", "")).strip()
    if not checkpoint:
        return ""
    checkpoint_path = _resolve_path(checkpoint)
    return str(checkpoint_path) if checkpoint_path.exists() else ""


def _metrics(summary: dict[str, Any], method: str = "best") -> dict[str, float]:
    if method == "baseline":
        payload = summary.get("methods", {}).get("baseline", {})
    elif method == "adapter":
        payload = summary.get("methods", {}).get("adapter", {})
    else:
        payload = summary.get("best_metrics", {})
        if not payload:
            payload = summary.get("methods", {}).get("adapter", {})
    return {
        "R@1": float(payload.get("R@1", 0.0)),
        "R@5": float(payload.get("R@5", 0.0)),
        "R@10": float(payload.get("R@10", 0.0)),
        "MedR": float(payload.get("MedR", 1e9)),
        "MnR": float(payload.get("MnR", 1e9)),
    }


def _quality_score(summary: dict[str, Any], reference: dict[str, Any] | None = None) -> dict[str, Any]:
    baseline = _metrics(summary, "baseline")
    best = _metrics(summary, "best")
    reference_metrics = _metrics(reference or {}, "best") if reference else baseline
    delta = {key: round(best[key] - baseline[key], 6) for key in ("R@1", "R@5", "R@10")}
    delta_vs_reference = {
        key: round(best[key] - reference_metrics[key], 6)
        for key in ("R@1", "R@5", "R@10")
    }
    memory = summary.get("memory_stats", {})
    if not isinstance(memory, dict):
        memory = {}
    no_recall_collapse = (
        delta_vs_reference["R@5"] >= -0.5
        and delta_vs_reference["R@10"] >= -0.5
    )
    positive_top1 = delta_vs_reference["R@1"] > 0.0
    memory_rate = float(memory.get("accepted_top1_is_gt_rate", 0.0) or 0.0)
    accepted = bool(positive_top1 and no_recall_collapse)
    score = (
        delta_vs_reference["R@1"] * 20.0
        + delta_vs_reference["R@5"] * 2.0
        + delta_vs_reference["R@10"]
        - max(0.0, -delta_vs_reference["R@5"]) * 4.0
        - max(0.0, -delta_vs_reference["R@10"]) * 3.0
        + memory_rate
    )
    return {
        "baseline": baseline,
        "best": best,
        "reference": reference_metrics,
        "delta_vs_run_baseline": delta,
        "delta_vs_active_best": delta_vs_reference,
        "quality_score": round(float(score), 6),
        "quality_accepted": accepted,
        "reason": (
            "R@1 is positive against active best and R@5/R@10 did not collapse."
            if accepted
            else "No reliable positive recall gain against active best."
        ),
        "memory_stats": memory,
    }


def _candidate_strategy(base: dict[str, Any], candidate_index: int) -> dict[str, Any]:
    strategy = dict(base)
    variants = [
        {},
        {
            "teacher_pairwise_weight": 1.25,
            "component_alignment_weight": 1.15,
            "alignment_teacher_weight": 1.10,
            "memory_augmented_weight": 0.90,
        },
        {
            "memory_augmented_weight": 1.25,
            "memory_refresh_topk": 1.25,
            "teacher_max_uncertainty": 1.003,
            "acceptance_max_uncertainty": 1.003,
            "teacher_min_margin": 0.85,
        },
        {
            "multiview_weight": 1.20,
            "alignment_teacher_weight": 0.90,
            "cross_modal_video_weight": 0.80,
            "teacher_pairwise_weight": 1.10,
        },
    ]
    variant = variants[(candidate_index - 1) % len(variants)]
    for key, multiplier in variant.items():
        if key in strategy and isinstance(strategy[key], (float, int)):
            value = strategy[key] * multiplier
            if key.endswith("uncertainty"):
                value = min(float(value), 0.999)
            if key == "memory_refresh_topk":
                value = int(round(value))
            strategy[key] = value
    return strategy


def _run(command: list[str], *, dry_run: bool) -> int:
    print(" ".join(command))
    if dry_run:
        return 0
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    return int(completed.returncode)


def _split_defaults(split: str) -> dict[str, str]:
    if split == "1kA":
        return {
            "eval_manifest": "msrvtt_fixed_1kA.jsonl",
            "eval_queries": "msrvtt_1kA_test_queries.jsonl",
        }
    return {
        "eval_manifest": "msrvtt_fixed_safe_dev.jsonl",
        "eval_queries": "msrvtt_train_9k_safe_dev_queries.jsonl",
    }


def _stage_command(
    *,
    args: argparse.Namespace,
    strategy: dict[str, Any],
    round_index: int,
    candidate_index: int,
    out_path: Path,
    max_train_queries: int,
    init_checkpoint: str,
) -> list[str]:
    split = _split_defaults(args.eval_split)
    command = [
        sys.executable,
        "-u",
        "scripts/run_stage_experiment.py",
        "--stage_label",
        f"auto_{args.strategy}_round{round_index:02d}_c{candidate_index:02d}",
        "--train_manifest",
        "msrvtt_fixed.jsonl",
        "--train_queries",
        "msrvtt_train_9k_safe_train_queries.jsonl",
        "--eval_manifest",
        split["eval_manifest"],
        "--eval_queries",
        split["eval_queries"],
        "--max_train_queries",
        str(max_train_queries),
        "--max_eval_queries",
        str(strategy["max_eval_queries"]),
        "--epochs",
        str(strategy["epochs"]),
        "--teacher_supervision",
        args.teacher_supervision,
        "--alignment_teacher",
        args.alignment_teacher,
        "--multiview_features",
        args.multiview_features,
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
        "--acceptance_alignment_weight",
        "1.0",
        "--uncertainty_aware_temperature",
        "--fuse_alphas",
        args.fuse_alphas,
        "--init_checkpoint",
        init_checkpoint,
        "--out",
        str(out_path),
    ]
    option_names = [
        "teacher_listwise_topk",
        "teacher_max_gt_rank",
        "teacher_max_uncertainty",
        "teacher_min_margin",
        "acceptance_max_teacher_rank",
        "acceptance_max_uncertainty",
        "memory_refresh_topk",
        "memory_augmented_weight",
        "alignment_teacher_weight",
        "multiview_weight",
        "component_alignment_weight",
        "teacher_pairwise_weight",
        "cross_modal_video_weight",
        "structured_prototype_weight",
        "video_aggregation_weight",
    ]
    for name in option_names:
        command.extend([f"--{name}", str(strategy[name])])
    return command


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


def _diagnosis_command(
    *,
    current_best: str,
    candidate_paths: list[Path],
    out: Path,
) -> list[str]:
    command = [
        sys.executable,
        "-u",
        "scripts/diagnose_continual_effect.py",
        "--current_best",
        current_best,
        "--out",
        str(out),
    ]
    for idx, path in enumerate(candidate_paths, start=1):
        command.extend(["--run", f"round{idx:02d}={path}"])
    return command


def _promotion_review(state_path: Path) -> dict[str, Any]:
    state = _read_json(state_path)
    review = state.get("candidate_review", {})
    if not isinstance(review, dict):
        review = {}
    return {
        "promoted": bool(review.get("promoted", False)),
        "reason": str(review.get("reason", "")),
        "candidate_metrics": review.get("candidate_metrics", {}),
        "previous_best_metrics": review.get("previous_best_metrics", {}),
        "active_best": state.get("current_best", {}),
    }


def _write_feedback(
    *,
    out_path: Path,
    run_id: str,
    strategy_name: str,
    strategy: dict[str, Any],
    eval_split: str,
    rounds: list[dict[str, Any]],
    diagnosis_path: Path,
    success_target: float,
) -> dict[str, Any]:
    public_accepted = [row for row in rounds if row.get("accepted")]
    promotion_accepted = [row for row in rounds if row.get("promoted")]
    success_rate = len(public_accepted) / max(1, len(rounds))
    promotion_rate = len(promotion_accepted) / max(1, len(rounds))
    target_rate = success_target
    payload = {
        "schema_version": "auto_continual_feedback_v2",
        "time": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "strategy": strategy_name,
        "strategy_description": strategy.get("description", ""),
        "paper_basis": strategy.get("papers", []),
        "eval_split": eval_split,
        "rounds": rounds,
        "quality_success_rate": round(success_rate, 6),
        "promotion_success_rate": round(promotion_rate, 6),
        "target_success_rate": target_rate,
        "target_met": success_rate >= target_rate,
        "diagnosis_json": str(diagnosis_path),
    }
    lines = [
        f"# Auto Continual Learning Feedback: {run_id}",
        "",
        f"- Strategy: `{strategy_name}`",
        f"- Basis: {', '.join(str(x) for x in strategy.get('papers', []))}",
        f"- Eval split: `{eval_split}`",
        f"- Quality success rate: {success_rate:.1%}",
        f"- Promotion success rate: {promotion_rate:.1%}",
        f"- Target 80% met: {'yes' if success_rate >= target_rate else 'no'}",
        "- Acceptance reference: active best summary, not the candidate run baseline",
        "",
        "## Round Results",
        "",
    ]
    for row in rounds:
        quality = row.get("quality", {})
        delta = quality.get("delta_vs_active_best", {})
        lines.extend([
            f"### Round {row.get('round')}",
            "",
            f"- Selected candidate: `{row.get('selected_candidate_label')}`",
            f"- Accepted by quality gate: {row.get('accepted')}",
            f"- Promoted by active-best gate: {row.get('promoted')}",
            f"- Delta vs active best: R@1 {delta.get('R@1')}, R@5 {delta.get('R@5')}, R@10 {delta.get('R@10')}",
            f"- Reason: {row.get('reason')}",
            "",
        ])
    lines.extend([
        "## Interpretation",
        "",
        "A round is useful only when it improves over the active best.",
        "Rejected candidates are logged but never overwrite the current best.",
        (
            "Use `v35_plus` when the goal is to improve the current 50.5 R@1 case. "
            "`safe_dev` runs are diagnostic and are not comparable with the locked 1kA number."
        ),
        "",
    ])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    out_path.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run acceptance-gated continual learning rounds."
    )
    parser.add_argument(
        "--strategy",
        choices=sorted(STRATEGIES),
        default="v35_plus",
        help="Learning strategy preset.",
    )
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument(
        "--eval_split",
        choices=["safe_dev", "1kA"],
        default="safe_dev",
        help="Use safe_dev for model selection by default; keep 1kA as the locked reporting split.",
    )
    parser.add_argument(
        "--current_best",
        default=(
            "outputs/tables/analysis/"
            "stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json"
        ),
    )
    parser.add_argument(
        "--teacher_supervision",
        default=(
            "outputs/tables/analysis/"
            "viclip_teacher_supervision_stage2_safe_train_q500_cov100_t20_v1.jsonl"
        ),
    )
    parser.add_argument(
        "--alignment_teacher",
        default=(
            "outputs/tables/analysis/"
            "multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl"
        ),
    )
    parser.add_argument(
        "--multiview_features",
        default=(
            "outputs/tables/analysis/"
            "multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz"
        ),
    )
    parser.add_argument("--fuse_alphas", default="0.88,0.90,0.92")
    parser.add_argument("--min_r1_gain", type=float, default=0.5)
    parser.add_argument(
        "--min_quality_r1_gain",
        type=float,
        default=0.01,
        help="Internal positive-learning threshold against the run baseline.",
    )
    parser.add_argument(
        "--success_target",
        type=float,
        default=0.80,
        help="Target quality-accepted round rate reported in the feedback file.",
    )
    parser.add_argument(
        "--out_dir",
        default="outputs/tables/analysis/auto_continual_learning",
    )
    parser.add_argument(
        "--log",
        default="outputs/feedback/auto_continual_learning_log.jsonl",
    )
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if args.rounds < 1:
        raise ValueError("--rounds must be >= 1")

    strategy = dict(STRATEGIES[args.strategy])
    run_id = f"{_timestamp()}_{args.strategy}_{args.eval_split}"
    out_dir = PROJECT_ROOT / args.out_dir / run_id
    log_path = PROJECT_ROOT / args.log
    candidate_paths: list[Path] = []
    round_reports: list[dict[str, Any]] = []
    active_current_best = args.current_best
    active_current_summary = _read_json(_resolve_path(active_current_best))
    teacher_qid_cap = _teacher_qid_count(args.teacher_supervision)

    _append_jsonl(
        log_path,
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "event": "auto_learning_start",
            "run_id": run_id,
            "strategy": args.strategy,
            "rounds": args.rounds,
            "eval_split": args.eval_split,
            "strategy_config": strategy,
            "strategy_description": strategy.get("description", ""),
            "paper_basis": strategy.get("papers", []),
        },
    )

    for round_index in range(1, args.rounds + 1):
        round_candidates: list[dict[str, Any]] = []
        candidates_per_round = int(strategy.get("candidates_per_round", 1))
        for candidate_index in range(1, candidates_per_round + 1):
            candidate_strategy = _candidate_strategy(strategy, candidate_index)
            candidate = out_dir / f"round{round_index:02d}_c{candidate_index:02d}_summary.json"
            candidate_paths.append(candidate)
            effective_max_train_queries = int(candidate_strategy["max_train_queries"])
            if teacher_qid_cap > 0:
                effective_max_train_queries = min(effective_max_train_queries, teacher_qid_cap)
            init_checkpoint = _checkpoint_from_summary(active_current_best)
            stage_command = _stage_command(
                args=args,
                strategy=candidate_strategy,
                round_index=round_index,
                candidate_index=candidate_index,
                out_path=candidate,
                max_train_queries=effective_max_train_queries,
                init_checkpoint=init_checkpoint,
            )
            return_code = _run(stage_command, dry_run=args.dry_run)
            summary = _read_json(candidate) if return_code == 0 and not args.dry_run else {}
            quality = _quality_score(summary, active_current_summary) if summary else {
                "quality_score": 0.0,
                "quality_accepted": False,
                "reason": "Dry run or summary missing.",
                "delta_vs_run_baseline": {},
                "delta_vs_active_best": {},
            }
            if quality.get("delta_vs_active_best", {}).get("R@1", 0.0) < args.min_quality_r1_gain:
                quality["quality_accepted"] = False
                quality["reason"] = (
                    "R@1 gain vs active best is below "
                    f"min_quality_r1_gain={args.min_quality_r1_gain}."
                )
            candidate_record = {
                "round": round_index,
                "candidate": candidate_index,
                "label": f"round{round_index:02d}_c{candidate_index:02d}",
                "summary": str(candidate),
                "return_code": return_code,
                "strategy_config": candidate_strategy,
                "effective_max_train_queries": effective_max_train_queries,
                "init_checkpoint": init_checkpoint,
                "quality": quality,
            }
            round_candidates.append(candidate_record)
            _append_jsonl(
                log_path,
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "event": "candidate_train_complete",
                    "run_id": run_id,
                    **candidate_record,
                },
            )
            if return_code != 0:
                raise RuntimeError(
                    f"Round {round_index} candidate {candidate_index} failed with code {return_code}"
                )

        selected = sorted(
            round_candidates,
            key=lambda item: float(item["quality"].get("quality_score", -1e9)),
            reverse=True,
        )[0]
        candidate = Path(selected["summary"])
        state_out = out_dir / f"round{round_index:02d}_continual_state.json"
        promote_command = _promotion_command(
            current_best=active_current_best,
            candidate=candidate,
            state_out=state_out,
            min_r1_gain=args.min_r1_gain,
        )
        return_code = _run(promote_command, dry_run=args.dry_run)
        promotion = _promotion_review(state_out) if return_code == 0 and not args.dry_run else {
            "promoted": False,
            "reason": "Dry run.",
        }
        if promotion.get("promoted"):
            active_best = promotion.get("active_best", {})
            if isinstance(active_best, dict) and active_best.get("summary_json"):
                active_current_best = str(active_best["summary_json"])
                active_current_summary = _read_json(_resolve_path(active_current_best))
        accepted = bool(selected["quality"].get("quality_accepted", False))
        reason = selected["quality"].get("reason", "")
        if not accepted:
            reason = f"Rejected by quality gate: {reason}"
        elif not promotion.get("promoted"):
            reason = (
                f"Quality gate passed; active-best gate did not promote: "
                f"{promotion.get('reason', '')}"
            )
        else:
            reason = f"Promoted: {promotion.get('reason', '')}"
        round_report = {
            "round": round_index,
            "selected_candidate_label": selected["label"],
            "selected_summary": selected["summary"],
            "all_candidates": round_candidates,
            "quality": selected["quality"],
            "accepted": accepted,
            "promoted": bool(promotion.get("promoted", False)),
            "promotion": promotion,
            "state": str(state_out),
            "reason": reason,
        }
        round_reports.append(round_report)
        _append_jsonl(
            log_path,
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "event": "round_gate_complete",
                "run_id": run_id,
                **round_report,
                "return_code": return_code,
            },
        )
        if return_code != 0:
            raise RuntimeError(
                f"Promotion gate for round {round_index} failed with code {return_code}"
            )

    diagnosis_out = out_dir / "diagnosis.json"
    diagnosis_command = _diagnosis_command(
        current_best=active_current_best,
        candidate_paths=candidate_paths,
        out=diagnosis_out,
    )
    return_code = _run(diagnosis_command, dry_run=args.dry_run)
    _append_jsonl(
        log_path,
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "event": "diagnosis_complete",
            "run_id": run_id,
            "diagnosis": str(diagnosis_out),
            "return_code": return_code,
        },
    )
    if return_code != 0:
        raise RuntimeError(f"Diagnosis failed with code {return_code}")

    feedback_path = out_dir / "learning_feedback.md"
    feedback = _write_feedback(
        out_path=feedback_path,
        run_id=run_id,
        strategy_name=args.strategy,
        strategy=strategy,
        eval_split=args.eval_split,
        rounds=round_reports,
        diagnosis_path=diagnosis_out,
        success_target=args.success_target,
    )
    if not args.dry_run:
        append_research_log(
            step="auto_continual_learning::feedback",
            summary=(
                f"Completed auto continual learning run {run_id} with strategy={args.strategy}; "
                f"quality_success_rate={feedback['quality_success_rate']}, "
                f"promotion_success_rate={feedback['promotion_success_rate']}."
            ),
            decisions=[
                f"Strategy description: {strategy.get('description', '')}",
                f"Eval split: {args.eval_split}",
                f"Rounds: {args.rounds}",
                f"Quality target 80% met: {feedback['target_met']}",
                "Rejected candidates are logged and do not overwrite the active best model.",
            ],
            citations=[
                "discovla_cvpr2025",
                "tokenbinder_wacv2025",
                "mama_arxiv2026",
                "fluxvit_iccv2025",
            ],
            artifacts=[
                str(feedback_path),
                str(feedback_path.with_suffix(".json")),
                str(diagnosis_out),
                str(log_path),
            ],
            extra=feedback,
        )
    _append_jsonl(
        log_path,
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "event": "feedback_complete",
            "run_id": run_id,
            "feedback_md": str(feedback_path),
            "feedback_json": str(feedback_path.with_suffix(".json")),
            "quality_success_rate": feedback["quality_success_rate"],
            "promotion_success_rate": feedback["promotion_success_rate"],
            "target_met": feedback["target_met"],
        },
    )
    print(f"[OK] auto continual learning run: {out_dir}")
    print(f"[OK] log: {log_path}")
    print(f"[OK] feedback: {feedback_path}")
    print(
        "Learning quality: "
        f"{feedback['quality_success_rate']:.1%} accepted, "
        f"{feedback['promotion_success_rate']:.1%} promoted, "
        f"target_80_met={feedback['target_met']}"
    )


if __name__ == "__main__":
    main()
