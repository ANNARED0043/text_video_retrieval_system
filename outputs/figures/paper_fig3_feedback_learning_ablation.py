from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "outputs" / "tables" / "analysis"
FIG_DIR = ROOT / "outputs" / "figures"


RUNS = [
    ("当前主模型", "stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json", "methods.adapter"),
    ("无反馈学习", "continual_ab_no_memory_1kA_train500_eval200_v1.json", "methods.adapter"),
    ("当前Memory", "continual_ab_current_memory_1kA_train500_eval200_v1.json", "methods.adapter"),
    ("严格Memory", "continual_ab_strict_memory_1kA_train500_eval200_v1.json", "methods.adapter"),
    ("放宽Memory", "continual_ab_relaxed_memory_1kA_train500_eval200_v1.json", "methods.adapter"),
    ("反馈Replay", "stage3_highquality_selected_q1500_replay_v35_recipe_eval1kAq200_v1.json", "augmented_methods.adapter"),
    ("近错Pairwise", "continual_nearmiss_rank2_5_from_v35_pairwise_eval1kAq200_v1.json", "methods.adapter"),
]


def _load_metric(file_name: str, key_path: str) -> dict:
    data = json.loads((ANALYSIS_DIR / file_name).read_text(encoding="utf-8"))
    node = data
    for key in key_path.split("."):
        node = node[key]
    return node


def _set_style() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": [
                "SimSun",
                "Microsoft YaHei",
                "Noto Sans CJK SC",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "axes.linewidth": 0.9,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.size": 4,
            "ytick.major.size": 4,
        }
    )


def main() -> None:
    _set_style()
    labels = []
    metrics = []
    for label, file_name, key_path in RUNS:
        labels.append(label)
        metrics.append(_load_metric(file_name, key_path))

    r1 = np.array([float(m["R@1"]) for m in metrics])
    r5 = np.array([float(m["R@5"]) for m in metrics])
    r10 = np.array([float(m["R@10"]) for m in metrics])
    mnr = np.array([float(m["MnR"]) for m in metrics])
    base = metrics[0]
    delta_r1 = r1 - float(base["R@1"])
    delta_r5 = r5 - float(base["R@5"])
    delta_r10 = r10 - float(base["R@10"])
    delta_mnr = mnr - float(base["MnR"])

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.2))
    x = np.arange(len(labels))
    width = 0.25

    ax = axes[0]
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.bar(x - width, delta_r1, width, label="ΔR@1", color="#4C78A8", edgecolor="black", linewidth=0.45)
    ax.bar(x, delta_r5, width, label="ΔR@5", color="#72B7B2", edgecolor="black", linewidth=0.45)
    ax.bar(x + width, delta_r10, width, label="ΔR@10", color="#F58518", edgecolor="black", linewidth=0.45)
    ax.set_title("(a) 相对当前主模型的 Recall 变化", fontsize=11)
    ax.set_ylabel("ΔRecall (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8.5)
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")

    ax = axes[1]
    colors = ["#9CA3AF" if v >= 0 else "#4C78A8" for v in delta_mnr]
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.bar(x, delta_mnr, color=colors, edgecolor="black", linewidth=0.45)
    ax.set_title("(b) 平均排名 MnR 变化（越低越好）", fontsize=11)
    ax.set_ylabel("ΔMnR")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8.5)
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7)
    ax.annotate(
        "反馈Replay：R@1持平\nR@5/R@10与MnR改善",
        xy=(5, delta_mnr[5]),
        xytext=(3.55, -0.34),
        arrowprops=dict(arrowstyle="->", linewidth=0.9, color="#111827"),
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#6B7280", lw=0.7),
    )

    for ax in axes:
        ax.set_axisbelow(True)

    fig.text(0.5, 0.01, "图3-7 错误驱动反馈学习机制消融结果", ha="center", fontsize=12)
    fig.tight_layout(rect=(0.01, 0.06, 0.99, 0.98))
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "paper_fig3_feedback_learning_ablation.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "paper_fig3_feedback_learning_ablation.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
