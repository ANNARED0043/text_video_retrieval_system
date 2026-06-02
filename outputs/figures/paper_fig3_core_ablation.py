from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "outputs" / "tables" / "analysis"
FIG_DIR = ROOT / "outputs" / "figures"


EXPERIMENTS = [
    (
        "基础召回",
        "baseline_vith14_mean_topk200_q200.json",
        "metrics",
    ),
    (
        "对齐教师",
        "stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1.json",
        "methods.adapter",
    ),
    (
        "门控对齐",
        "stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2.json",
        "methods.adapter",
    ),
    (
        "教师目标增强",
        "stage3_alignment_teacher_train_targets_1kA_f6_v33.json",
        "methods.adapter",
    ),
    (
        "对齐+多视角",
        "stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json",
        "methods.adapter",
    ),
    (
        "扩大样本筛选",
        "stage3_highquality_selected_componentview_vtokens6_align_multiview_pairwise_queryaware_q1500_eval1kAq200_v1.json",
        "methods.adapter",
    ),
]


def _load_metrics(file_name: str, key_path: str) -> dict:
    data = json.loads((ANALYSIS_DIR / file_name).read_text(encoding="utf-8"))
    node = data
    for key in key_path.split("."):
        node = node[key]
    return node


def _set_paper_style() -> None:
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
    _set_paper_style()
    labels = []
    r1, r5, r10, medr = [], [], [], []
    for label, file_name, key_path in EXPERIMENTS:
        metrics = _load_metrics(file_name, key_path)
        labels.append(label)
        r1.append(float(metrics["R@1"]))
        r5.append(float(metrics["R@5"]))
        r10.append(float(metrics["R@10"]))
        medr.append(float(metrics["MedR"]))

    x = np.arange(len(labels))
    width = 0.22
    colors = ["#4C78A8", "#72B7B2", "#F58518"]

    fig, ax = plt.subplots(figsize=(10.2, 4.8))
    bars1 = ax.bar(x - width, r1, width, label="R@1", color=colors[0], edgecolor="black", linewidth=0.5)
    ax.bar(x, r5, width, label="R@5", color=colors[1], edgecolor="black", linewidth=0.5)
    ax.bar(x + width, r10, width, label="R@10", color=colors[2], edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Recall (%)", fontsize=12)
    ax.set_ylim(40, 78)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=10)

    best_idx = labels.index("对齐+多视角")
    ax.annotate(
        "当前主方法\nR@1=50.5",
        xy=(best_idx - width, r1[best_idx]),
        xytext=(best_idx - 0.6, 55.5),
        arrowprops=dict(arrowstyle="->", color="#1F2937", linewidth=1.0),
        fontsize=10,
        ha="center",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#6B7280", lw=0.8),
    )

    for rect in bars1:
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            height + 0.45,
            f"{height:.1f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#111827",
        )

    ax2 = ax.twinx()
    ax2.plot(x, medr, color="#111827", marker="o", linewidth=1.5, markersize=4.5, label="MedR")
    ax2.set_ylabel("MedR", fontsize=12)
    ax2.set_ylim(0.5, 2.3)
    ax2.tick_params(axis="y", labelsize=10)
    ax2.legend(frameon=False, loc="upper right", fontsize=10)

    fig.text(
        0.5,
        0.01,
        "图3-4 细粒度表征增强核心消融结果（1kA q200，用于方法消融验证）",
        ha="center",
        fontsize=12,
    )
    fig.tight_layout(rect=(0.02, 0.06, 0.98, 0.98))

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "paper_fig3_core_ablation.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "paper_fig3_core_ablation.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
