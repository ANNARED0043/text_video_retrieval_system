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


METRIC_KEYS = ("R@1", "R@5", "R@10", "MedR", "MnR")
MEMORY_KEYS = (
    "accepted",
    "acceptance_rate",
    "accepted_gt_rank_mean",
    "accepted_top1_is_gt_rate",
    "accepted_uncertainty_mean",
    "accepted_alignment_overlap_mean",
)


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


def _metrics(summary: dict[str, Any]) -> dict[str, float]:
    payload = summary.get("methods", {}).get("adapter", {})
    if not payload:
        payload = summary.get("best_metrics", {})
    return {key: float(payload.get(key, 0.0)) for key in METRIC_KEYS}


def _memory(summary: dict[str, Any]) -> dict[str, Any]:
    payload = summary.get("memory_stats", {})
    if not isinstance(payload, dict):
        return {}
    return {key: payload.get(key) for key in MEMORY_KEYS if key in payload}


def _delta(candidate: dict[str, float], reference: dict[str, float]) -> dict[str, float]:
    return {key: round(candidate[key] - reference[key], 6) for key in METRIC_KEYS}


def _parse_run(item: str) -> tuple[str, Path]:
    if "=" not in item:
        path = _resolve_path(item)
        return path.stem, path
    label, path_text = item.split("=", 1)
    return label.strip(), _resolve_path(path_text.strip())


def _is_not_worse(candidate: dict[str, float], reference: dict[str, float]) -> bool:
    return (
        candidate["R@1"] >= reference["R@1"]
        and candidate["R@5"] >= reference["R@5"]
        and candidate["R@10"] >= reference["R@10"]
        and candidate["MedR"] <= reference["MedR"]
    )


def _best_label(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    best = sorted(
        rows,
        key=lambda row: (
            row["metrics"]["R@1"],
            row["metrics"]["R@5"],
            row["metrics"]["R@10"],
            -row["metrics"]["MedR"],
            -row["metrics"]["MnR"],
        ),
        reverse=True,
    )[0]
    return str(best["label"])


def _diagnose(rows: list[dict[str, Any]], current_best: dict[str, float]) -> list[str]:
    by_label = {row["label"]: row for row in rows}
    findings: list[str] = []
    no_memory = by_label.get("no_memory")
    current_memory = by_label.get("current_memory")
    strict_memory = by_label.get("strict_memory")
    relaxed_memory = by_label.get("relaxed_memory")
    has_named_ablation = any(item is not None for item in (no_memory, current_memory, strict_memory, relaxed_memory))

    if rows and not has_named_ablation:
        best = _best_label(rows)
        if best:
            findings.append(f"本组自动学习最优 candidate 是 {best}。")
        improved = [
            row["label"] for row in rows
            if row["metrics"]["R@1"] > current_best["R@1"]
        ]
        if improved:
            findings.append(f"存在超过当前最佳 R@1 的候选：{', '.join(improved)}。")
        else:
            findings.append("本组自动学习没有候选超过当前最佳 R@1。")
        recall_improved = [
            row["label"] for row in rows
            if row["metrics"]["R@5"] >= current_best["R@5"]
            and row["metrics"]["R@10"] >= current_best["R@10"]
        ]
        if recall_improved:
            findings.append(f"这些候选提升了更宽召回：{', '.join(recall_improved)}。")
        else:
            findings.append("本组候选在更宽召回上也没有形成稳定优势。")
        return findings

    if no_memory and current_memory:
        r1_gain = current_memory["metrics"]["R@1"] - no_memory["metrics"]["R@1"]
        if r1_gain > 0:
            findings.append(
                f"memory 有正向证据：current_memory 比 no_memory 的 R@1 高 {r1_gain:.2f}。"
            )
        else:
            findings.append(
                "memory 未显示正向证据：current_memory 没有超过 no_memory，需调整学习策略。"
            )
        if current_memory["metrics"]["R@5"] < no_memory["metrics"]["R@5"]:
            findings.append(
                "注意：memory 提升 R@1 的同时降低了 R@5，说明它更偏 top1 校准，泛化召回仍需改进。"
            )
        if current_memory["metrics"]["R@10"] < no_memory["metrics"]["R@10"]:
            findings.append(
                "注意：memory 降低了 R@10，说明候选覆盖层面的收益不足，不能只依赖当前 memory gate。"
            )

    if strict_memory and current_memory:
        if strict_memory["metrics"]["R@1"] < current_memory["metrics"]["R@1"]:
            findings.append("strict_memory 变差：gate 过严会减少有效训练样本，不建议收紧到当前设置。")
        else:
            findings.append("strict_memory 没有伤害 R@1：可以考虑更高质量 memory。")

    if relaxed_memory and current_memory:
        if relaxed_memory["metrics"]["R@1"] > current_memory["metrics"]["R@1"]:
            findings.append("relaxed_memory 更好：当前 memory 数量不足，可以扩大 accepted 样本。")
        elif relaxed_memory["metrics"]["R@1"] < current_memory["metrics"]["R@1"]:
            findings.append("relaxed_memory 变差：放宽 gate 引入噪声，不建议扩大到当前设置。")
        else:
            findings.append("relaxed_memory 与 current_memory 持平：需要用 feedback set 再判断是否值得放宽。")
    elif relaxed_memory is None:
        findings.append("relaxed_memory 缺失：第四轮没有生成 summary，无法判断放宽 gate 的效果。")

    best = _best_label(rows)
    if best:
        findings.append(f"本组实验最优 candidate 是 {best}。")

    for row in rows:
        if _is_not_worse(row["metrics"], current_best):
            findings.append(f"{row['label']} 没有低于 fixed reference，可作为候选继续观察。")

    if not findings:
        findings.append("没有足够结果做诊断。")
    return findings


def diagnose(
    *,
    current_best_path: str,
    runs: list[str],
    out: str,
) -> None:
    current_summary = _read_json(_resolve_path(current_best_path))
    if not current_summary:
        raise FileNotFoundError(f"Cannot read current best: {current_best_path}")
    current_metrics = _metrics(current_summary)

    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for item in runs:
        label, path = _parse_run(item)
        summary = _read_json(path)
        if not summary:
            missing.append(f"{label}={path}")
            continue
        metrics = _metrics(summary)
        rows.append({
            "label": label,
            "path": str(path),
            "metrics": metrics,
            "delta_vs_current_best": _delta(metrics, current_metrics),
            "memory_stats": _memory(summary),
        })

    report = {
        "schema_version": "continual_effect_diagnosis_v1",
        "time": datetime.now().isoformat(timespec="seconds"),
        "current_best": {
            "path": str(_resolve_path(current_best_path)),
            "metrics": current_metrics,
        },
        "runs": rows,
        "missing_runs": missing,
        "diagnosis": _diagnose(rows, current_metrics),
        "learning_effect_criteria": {
            "memory_quantity": "accepted should increase without severe uncertainty degradation.",
            "memory_quality": "accepted_gt_rank_mean should decrease and accepted_top1_is_gt_rate should rise.",
            "no_forgetting": "fixed reference metrics should not drop.",
            "feedback_gain": "a held-out or newly collected feedback set should improve across rounds.",
            "recall_gain": "R@5/R@10 should eventually improve before reliable R@1 gains.",
        },
        "next_action_rule": (
            "If current_memory beats no_memory only on R@1 but hurts R@5/R@10, keep v3.5 as best "
            "and redesign continual learning around feedback/replay rather than only changing gate thresholds."
        ),
    }

    out_path = _resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    append_research_log(
        step="continual_layer::effect_diagnosis",
        summary="已完成 Continual Layer 多轮效果诊断：不只检查晋升，还检查 memory 是否真实带来正向学习信号。",
        decisions=report["diagnosis"],
        citations=["discovla_cvpr2025", "mv_adapter_cvpr2024", "teachclip_cvpr2024"],
        artifacts=[str(out_path)],
        extra=report,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose whether continual-learning rounds are genuinely useful.")
    parser.add_argument("--current_best", type=str, required=True)
    parser.add_argument("--run", action="append", default=[], help="Format: label=summary_json")
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    diagnose(current_best_path=args.current_best, runs=args.run, out=args.out)


if __name__ == "__main__":
    main()
