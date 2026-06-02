"""Draw publication-style figures for the thesis.

The script reads experiment summaries from ``outputs/tables/analysis`` and
exports high-resolution figures to ``outputs/figures``. Missing optional files
fall back to values recorded in the research log, so the script remains useful
even if a few historical summaries were produced outside the current run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "outputs" / "tables" / "analysis"
FIGURE_DIR = ROOT / "outputs" / "figures"


def _load_json(name: str) -> dict[str, Any]:
    path = ANALYSIS_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _method_metrics(data: dict[str, Any], method: str = "adapter") -> dict[str, float]:
    if "metrics" in data and isinstance(data["metrics"], dict):
        return data["metrics"]
    if method in data and isinstance(data[method], dict):
        return data[method]
    if "methods" in data and method in data["methods"]:
        return data["methods"][method]
    return data


def _metric(data: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(data[key])
    except (KeyError, TypeError, ValueError):
        return default


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linestyle": "--",
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _save(fig: plt.Figure, name: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".pdf"):
        fig.savefig(FIGURE_DIR / f"{name}{suffix}", bbox_inches="tight")
    plt.close(fig)


def draw_fig5_1_baseline_candidate_recall() -> None:
    baseline = _load_json("baseline_vith14_mean_topk200_q200.json")
    candidate = _load_json("baseline_vith14_candidate_recall_top30_1kA_full.json")
    labels = ["R@1", "R@5", "R@10", "R@30"]
    baseline_values = [
        _metric(baseline, "R@1", 47.5),
        _metric(baseline, "R@5", 65.0),
        _metric(baseline, "R@10", 72.0),
        np.nan,
    ]
    candidate_values = [
        _metric(candidate, "R@1", 39.0),
        _metric(candidate, "R@5", 61.86),
        _metric(candidate, "R@10", 71.24),
        _metric(candidate, "R@30", 83.78),
    ]

    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    bars_a = ax.bar(x - width / 2, baseline_values, width, label="Video-level baseline",
                    color="#4C78A8")
    bars_b = ax.bar(x + width / 2, candidate_values, width, label="Candidate recall",
                    color="#F58518")
    ax.set_ylabel("Recall (%)")
    ax.set_ylim(0, 90)
    ax.set_xticks(x, labels)
    ax.set_title("Baseline Retrieval and Candidate Recall on Locked 1kA")
    ax.legend(loc="upper left")
    for bars in (bars_a, bars_b):
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
    _save(fig, "paper_fig5_1_baseline_candidate_recall")


def draw_fig5_2_alignment_progression() -> None:
    files = [
        ("F6", "stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1.json"),
        ("F6+Gate", "stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2.json"),
        ("F6+Targets", "stage3_alignment_teacher_train_targets_1kA_f6_v33.json"),
        ("Multiview", "stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json"),
    ]
    labels, r1, r5, r10 = [], [], [], []
    fallbacks = {
        "F6": (49.0, 66.0, 73.5),
        "F6+Gate": (49.5, 65.5, 73.5),
        "F6+Targets": (50.0, 64.5, 74.0),
        "Multiview": (50.5, 64.5, 73.5),
    }
    for label, name in files:
        metrics = _method_metrics(_load_json(name), "adapter")
        fb = fallbacks[label]
        labels.append(label)
        r1.append(_metric(metrics, "R@1", fb[0]))
        r5.append(_metric(metrics, "R@5", fb[1]))
        r10.append(_metric(metrics, "R@10", fb[2]))

    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    ax.plot(labels, r1, marker="o", linewidth=2.0, label="R@1", color="#C44E52")
    ax.plot(labels, r5, marker="s", linewidth=1.8, label="R@5", color="#4C78A8")
    ax.plot(labels, r10, marker="^", linewidth=1.8, label="R@10", color="#59A14F")
    ax.set_ylabel("Recall (%)")
    ax.set_ylim(45, 77)
    ax.set_title("Progression of Fine-grained Alignment Enhancement")
    ax.legend(loc="lower right", ncol=3)
    for idx, val in enumerate(r1):
        ax.annotate(f"{val:.1f}", (idx, val), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8)
    _save(fig, "paper_fig5_2_alignment_progression")


def draw_fig5_3_main_results() -> None:
    baseline = _load_json("baseline_vith14_mean_topk200_q200.json")
    multiview = _method_metrics(
        _load_json("stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json"),
        "adapter",
    )
    loop = _method_metrics(_load_json("error_driven_round01_1kA_eval.json"), "adapter")
    data = {
        "Baseline": baseline or {"R@1": 47.5, "R@5": 65.0, "R@10": 72.0},
        "Alignment+Multiview": multiview or {"R@1": 50.5, "R@5": 64.5, "R@10": 73.5},
        "Feedback Candidate": loop or {"R@1": 48.5, "R@5": 66.5, "R@10": 74.0},
    }
    metrics = ["R@1", "R@5", "R@10"]
    x = np.arange(len(metrics))
    width = 0.24
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    colors = ["#4C78A8", "#C44E52", "#59A14F"]
    for idx, (name, values) in enumerate(data.items()):
        y = [_metric(values, metric) for metric in metrics]
        bars = ax.bar(x + (idx - 1) * width, y, width, label=name, color=colors[idx])
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
    ax.set_xticks(x, metrics)
    ax.set_ylabel("Recall (%)")
    ax.set_ylim(40, 78)
    ax.set_title("Main Locked 1kA Results")
    ax.legend(loc="upper left")
    _save(fig, "paper_fig5_3_main_results")


def draw_fig5_4_safe_dev_loop_gain() -> None:
    reference = _method_metrics(
        _load_json(
            "error_driven_agent_loop/20260424_163109_error_driven_safe_dev/"
            "reference_current_best_eval.json"
        ),
        "adapter",
    )
    round_1 = _method_metrics(
        _load_json(
            "error_driven_agent_loop/20260424_163109_error_driven_safe_dev/"
            "round01_summary.json"
        ),
        "adapter",
    )
    if not reference:
        reference = {"R@1": 40.0, "R@5": 60.0, "R@10": 71.5}
    if not round_1:
        round_1 = {"R@1": 40.5, "R@5": 62.5, "R@10": 72.0}

    metrics = ["R@1", "R@5", "R@10"]
    before = [_metric(reference, m) for m in metrics]
    after = [_metric(round_1, m) for m in metrics]
    x = np.arange(len(metrics))
    fig, ax = plt.subplots(figsize=(5.8, 3.5))
    ax.plot(x, before, marker="o", label="Before loop", color="#4C78A8")
    ax.plot(x, after, marker="o", label="After round 1", color="#C44E52")
    ax.fill_between(x, before, after, color="#C44E52", alpha=0.12)
    ax.set_xticks(x, metrics)
    ax.set_ylabel("Recall (%)")
    ax.set_ylim(35, 76)
    ax.set_title("Safe-dev Feedback Loop Improvement")
    ax.legend(loc="lower right")
    _save(fig, "paper_fig5_4_safe_dev_loop_gain")


def draw_fig5_5_failure_distribution() -> None:
    data = _load_json("failure_diagnosis_v35_1kA_q200.json")
    tags = data.get("failure_tags") or {
        "object": 72,
        "relation": 67,
        "person_attribute": 53,
        "action": 43,
        "scene": 14,
        "other": 12,
        "multi_action": 7,
        "temporal_order": 3,
    }
    items = sorted(tags.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in items]
    values = [item[1] for item in items]
    fig, ax = plt.subplots(figsize=(6.5, 3.7))
    bars = ax.barh(labels[::-1], values[::-1], color="#4C78A8")
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel("Failure count")
    ax.set_title("Failure Type Distribution of the Best Locked 1kA Model")
    _save(fig, "paper_fig5_5_failure_distribution")


def main() -> None:
    _setup_style()
    draw_fig5_1_baseline_candidate_recall()
    draw_fig5_2_alignment_progression()
    draw_fig5_3_main_results()
    draw_fig5_4_safe_dev_loop_gain()
    draw_fig5_5_failure_distribution()
    print(f"[OK] wrote thesis figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
