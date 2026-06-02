from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_stage_experiment import _acceptance_score, _load_alignment_teacher
from src.learning.teacher_supervision import load_teacher_supervision, write_teacher_supervision


def _read_jsonl(path: Path, limit: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit > 0 and len(rows) >= limit:
                break
    return rows


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    root_path = PROJECT_ROOT / path
    if root_path.exists():
        return root_path
    data_path = PROJECT_ROOT / "data" / "annotations" / "msrvtt" / path
    if data_path.exists():
        return data_path
    return root_path


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(np.mean(values)), 6)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(np.median(values)), 6)


def _quality_tier(meta: dict[str, Any]) -> str:
    rank = meta.get("teacher_gt_rank")
    uncertainty = float(meta.get("uncertainty", 1.0))
    alignment = float(meta.get("alignment_overlap", 0.0))
    prototype = float(meta.get("prototype_overlap", 0.0))
    overlap = max(alignment, prototype)
    if rank is not None and rank <= 5 and uncertainty <= 0.98 and overlap > 0:
        return "A_strict"
    if rank is not None and rank <= 10 and uncertainty <= 0.99:
        return "B_reliable"
    if rank is not None and rank <= 20 and uncertainty <= 0.995:
        return "C_usable"
    return "D_weak"


def diagnose(args: argparse.Namespace) -> dict[str, Any]:
    query_rows = _read_jsonl(_resolve(args.train_queries), args.max_train_queries)
    teacher_entries = load_teacher_supervision(_resolve(args.teacher_supervision))
    alignment_teacher = _load_alignment_teacher(args.alignment_teacher)

    accepted: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    rejected_reasons: Counter[str] = Counter()
    tiers: Counter[str] = Counter()
    all_gt_ranks: list[float] = []
    accepted_gt_ranks: list[float] = []
    accepted_uncertainties: list[float] = []
    accepted_alignment: list[float] = []
    accepted_prototype: list[float] = []

    for row in query_rows:
        qid = str(row.get("qid", ""))
        entry = teacher_entries.get(qid)
        score, meta = _acceptance_score(
            row,
            entry,
            max_teacher_rank=args.max_teacher_rank,
            max_uncertainty=args.max_uncertainty,
            min_overlap=args.min_overlap,
            alignment_teacher=alignment_teacher,
            alignment_weight=args.alignment_weight,
        )
        gt_rank = meta.get("teacher_gt_rank")
        if gt_rank is not None:
            all_gt_ranks.append(float(gt_rank))
        if score > 0:
            tiers[_quality_tier(meta)] += 1
            accepted.append((score, row, meta))
            accepted_gt_ranks.append(float(gt_rank))
            accepted_uncertainties.append(float(meta.get("uncertainty", 1.0)))
            accepted_alignment.append(float(meta.get("alignment_overlap", 0.0)))
            accepted_prototype.append(float(meta.get("prototype_overlap", 0.0)))
        else:
            rejected_reasons[str(meta.get("reason", "unknown"))] += 1

    accepted.sort(key=lambda item: item[0], reverse=True)
    selected = accepted[: args.memory_topk] if args.memory_topk > 0 else accepted
    selected_scores = [float(item[0]) for item in selected]
    selected_ranks = [float(item[2].get("teacher_gt_rank")) for item in selected]
    selected_uncertainties = [float(item[2].get("uncertainty", 1.0)) for item in selected]
    selected_qids = [str(item[1].get("qid", "")) for item in selected]

    result = {
        "schema_version": "high_quality_learning_pool_diagnosis_v1",
        "train_queries": args.train_queries,
        "teacher_supervision": args.teacher_supervision,
        "alignment_teacher": args.alignment_teacher or "",
        "thresholds": {
            "max_teacher_rank": args.max_teacher_rank,
            "max_uncertainty": args.max_uncertainty,
            "min_overlap": args.min_overlap,
            "alignment_weight": args.alignment_weight,
            "memory_topk": args.memory_topk,
        },
        "candidates": len(query_rows),
        "teacher_entries": len(teacher_entries),
        "accepted_before_topk": len(accepted),
        "selected_after_topk": len(selected),
        "target_effective_samples": args.target_effective_samples,
        "target_met": len(selected) >= args.target_effective_samples,
        "acceptance_rate_before_topk": round(len(accepted) / max(1, len(query_rows)), 6),
        "selected_rate": round(len(selected) / max(1, len(query_rows)), 6),
        "quality_tiers": dict(tiers),
        "rejected_reasons": dict(rejected_reasons),
        "all_teacher_gt_rank_mean": _mean(all_gt_ranks),
        "all_teacher_gt_rank_median": _median(all_gt_ranks),
        "accepted_gt_rank_mean": _mean(accepted_gt_ranks),
        "accepted_gt_rank_median": _median(accepted_gt_ranks),
        "accepted_uncertainty_mean": _mean(accepted_uncertainties),
        "accepted_alignment_overlap_mean": _mean(accepted_alignment),
        "accepted_prototype_overlap_mean": _mean(accepted_prototype),
        "selected_acceptance_score_mean": _mean(selected_scores),
        "selected_gt_rank_mean": _mean(selected_ranks),
        "selected_uncertainty_mean": _mean(selected_uncertainties),
        "selected_qids": selected_qids,
        "next_action": (
            "Enough high-quality samples are available; run the filtered learning experiment."
            if len(selected) >= args.target_effective_samples
            else "Increase max_train_queries or relax rank/uncertainty thresholds before training."
        ),
    }

    if args.out_teacher_subset:
        teacher_subset_path = _resolve(args.out_teacher_subset)
        selected_entries = [
            teacher_entries[qid]
            for qid in selected_qids
            if qid in teacher_entries
        ]
        write_teacher_supervision(teacher_subset_path, selected_entries)
        result["out_teacher_subset"] = str(teacher_subset_path)

    if args.out_query_subset:
        query_subset_path = _resolve(args.out_query_subset)
        selected_qid_set = set(selected_qids)
        selected_rows = [
            row
            for row in query_rows
            if str(row.get("qid", "")) in selected_qid_set
        ]
        query_subset_path.parent.mkdir(parents=True, exist_ok=True)
        with query_subset_path.open("w", encoding="utf-8") as handle:
            for row in selected_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        result["out_query_subset"] = str(query_subset_path)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diagnose whether teacher supervision can provide enough high-quality learning samples."
    )
    parser.add_argument("--train_queries", required=True)
    parser.add_argument("--teacher_supervision", required=True)
    parser.add_argument("--alignment_teacher", default="")
    parser.add_argument("--max_train_queries", type=int, default=0)
    parser.add_argument("--max_teacher_rank", type=int, default=20)
    parser.add_argument("--max_uncertainty", type=float, default=0.995)
    parser.add_argument("--min_overlap", type=float, default=0.0)
    parser.add_argument("--alignment_weight", type=float, default=1.0)
    parser.add_argument("--memory_topk", type=int, default=500)
    parser.add_argument("--target_effective_samples", type=int, default=500)
    parser.add_argument("--out", default="")
    parser.add_argument("--out_teacher_subset", default="")
    parser.add_argument("--out_query_subset", default="")
    args = parser.parse_args()

    result = diagnose(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out_path = _resolve(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] wrote diagnosis: {out_path}")


if __name__ == "__main__":
    main()
