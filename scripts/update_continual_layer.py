from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.research_log import append_research_log
from src.utils.stage_status import write_current_stage


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _public_metrics(summary: dict[str, Any]) -> dict[str, float]:
    metrics = summary.get("methods", {}).get("adapter", {})
    if not metrics:
        metrics = summary.get("best_metrics", {})
    return {
        "R@1": float(metrics.get("R@1", 0.0)),
        "R@5": float(metrics.get("R@5", 0.0)),
        "R@10": float(metrics.get("R@10", 0.0)),
        "MnR": float(metrics.get("MnR", 1e9)),
        "MedR": float(metrics.get("MedR", 1e9)),
    }


def _should_promote(
    current: dict[str, float],
    candidate: dict[str, float],
    min_r1_gain: float,
) -> tuple[bool, str]:
    r1_gain = candidate["R@1"] - current["R@1"]
    if r1_gain >= min_r1_gain:
        return True, f"R@1 improved by {r1_gain:.4f}."
    if abs(r1_gain) < 1e-9:
        if candidate["MedR"] < current["MedR"]:
            return True, "R@1 tied and MedR improved."
        if candidate["MedR"] == current["MedR"] and candidate["MnR"] < current["MnR"]:
            return True, "R@1/MedR tied and MnR improved."
    return False, f"Candidate did not beat current best R@1={current['R@1']}."


def _memory_stats(summary: dict[str, Any]) -> dict[str, Any]:
    stats = summary.get("memory_stats", {})
    return stats if isinstance(stats, dict) else {}


def update_continual_layer(
    *,
    current_best: str,
    candidate: str,
    out: str,
    min_r1_gain: float,
) -> None:
    current_path = _resolve_path(current_best)
    candidate_path = _resolve_path(candidate) if candidate.strip() else current_path
    out_path = _resolve_path(out)

    current_summary = _read_json(current_path)
    candidate_summary = _read_json(candidate_path)
    if not current_summary:
        raise FileNotFoundError(f"Current best summary not found or empty: {current_path}")
    if not candidate_summary:
        raise FileNotFoundError(f"Candidate summary not found or empty: {candidate_path}")

    current_metrics = _public_metrics(current_summary)
    candidate_metrics = _public_metrics(candidate_summary)
    promoted, reason = _should_promote(current_metrics, candidate_metrics, min_r1_gain)
    active_summary = candidate_summary if promoted else current_summary
    active_path = candidate_path if promoted else current_path
    active_metrics = candidate_metrics if promoted else current_metrics

    artifacts = active_summary.get("artifacts", {}) if isinstance(active_summary.get("artifacts"), dict) else {}
    state = {
        "schema_version": "continual_layer_state_v1",
        "time": datetime.now().isoformat(timespec="seconds"),
        "active_stage": "Stage 3: Continual Learning and Memory",
        "policy": {
            "mode": "acceptance_gated_promotion",
            "min_r1_gain": min_r1_gain,
            "tie_breakers": ["lower MedR", "lower MnR"],
            "do_not_promote_if": [
                "candidate lowers R@1",
                "candidate only improves auxiliary losses",
                "candidate uses 1kA gt as training signal",
            ],
        },
        "current_best": {
            "summary_json": str(active_path),
            "stage_label": active_summary.get("stage_label", ""),
            "best_method": active_summary.get("best_method", ""),
            "metrics": active_metrics,
            "checkpoint": artifacts.get("checkpoint", ""),
            "memory_json": artifacts.get("stage3_memory_json", ""),
            "alignment_teacher": artifacts.get("alignment_teacher", ""),
            "multiview_features": artifacts.get("multiview_features", ""),
        },
        "candidate_review": {
            "candidate_json": str(candidate_path),
            "candidate_metrics": candidate_metrics,
            "previous_best_json": str(current_path),
            "previous_best_metrics": current_metrics,
            "promoted": promoted,
            "reason": reason,
        },
        "memory_quality": _memory_stats(active_summary),
        "next_round_rule": (
            "Use safe_train for learning, safe_dev for model selection, and 1kA only as locked reporting. "
            "A new continual round must write a candidate summary first, then pass this promotion gate."
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    write_current_stage(
        "stage3",
        "Continual Layer active: keep the current best model locked and only promote future candidates through acceptance-gated metrics.",
    )
    append_research_log(
        step="continual_layer::state_update",
        summary=(
            "Continual Layer 已启用：当前通过 acceptance-gated promotion 维护最优模型、"
            "memory 快照和后续晋升规则，不再让未超过当前最佳的 candidate 覆盖活动版本。"
        ),
        decisions=[
            f"Active best summary: {state['current_best']['summary_json']}",
            f"Active best metrics: {active_metrics}",
            f"Candidate promoted: {promoted}; reason: {reason}",
            f"State file: {out_path}",
            "后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。",
        ],
        citations=["discovla_cvpr2025", "mv_adapter_cvpr2024", "teachclip_cvpr2024"],
        artifacts=[str(out_path), str(active_path)],
        extra=state,
    )
    print(json.dumps(state, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Maintain the continual-learning active-best state."
    )
    parser.add_argument("--current_best", type=str, required=True)
    parser.add_argument("--candidate", type=str, default="")
    parser.add_argument(
        "--out",
        type=str,
        default="outputs/tables/analysis/continual_layer_state.json",
    )
    parser.add_argument("--min_r1_gain", type=float, default=0.5)
    args = parser.parse_args()
    update_continual_layer(
        current_best=args.current_best,
        candidate=args.candidate,
        out=args.out,
        min_r1_gain=args.min_r1_gain,
    )


if __name__ == "__main__":
    main()
