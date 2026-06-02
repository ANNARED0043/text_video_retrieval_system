from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "outputs" / "tables" / "analysis"
FIG_DIR = ROOT / "outputs" / "figures"


def _load_json(name: str) -> dict:
    return json.loads((ANALYSIS_DIR / name).read_text(encoding="utf-8"))


def _metric(data: dict, method: str, key: str) -> float:
    if "methods" in data:
        return float(data["methods"][method][key])
    if method == "metrics":
        return float(data["metrics"][key])
    return float(data[key])


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
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.1))

    # (a) Candidate recall and marginal gain.
    recall = _load_json("baseline_vith14_candidate_recall_curve_1kA_full.json")
    ks = [p["k"] for p in recall["recall_points"]]
    vals = [p["recall"] for p in recall["recall_points"]]
    gains_x = [g["to_k"] for g in recall["incremental_gains"]]
    gains = [g["gain"] for g in recall["incremental_gains"]]

    ax = axes[0]
    ax.plot(ks, vals, marker="o", color="#2F5597", linewidth=1.8, label="候选召回率")
    ax.bar(gains_x, gains, width=3.0, color="#B7C9E2", edgecolor="#2F5597", linewidth=0.5, label="边际增益")
    ax.axvline(30, color="#8B1A1A", linestyle="--", linewidth=1.0)
    ax.text(31, 53, "Top-30 后\n增益变缓", fontsize=9, color="#8B1A1A")
    ax.set_title("(a) 候选范围选择", fontsize=11)
    ax.set_xlabel("候选数 K")
    ax.set_ylabel("Recall / Gain (%)")
    ax.set_ylim(0, 95)
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    # (b) Pooling comparison.
    mean_d = _load_json("pooling_smoke200_mean_topk200.json")["metrics"]
    max_d = _load_json("pooling_smoke200_max_topk200.json")["metrics"]
    metrics = ["R@1", "R@5", "R@10"]
    x = np.arange(len(metrics))
    width = 0.34
    ax = axes[1]
    ax.bar(x - width / 2, [mean_d[m] for m in metrics], width, label="mean pooling", color="#4C78A8", edgecolor="black", linewidth=0.5)
    ax.bar(x + width / 2, [max_d[m] for m in metrics], width, label="max pooling", color="#F58518", edgecolor="black", linewidth=0.5)
    ax.set_title("(b) 视频级聚合选择", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylim(35, 90)
    ax.set_ylabel("Recall (%)")
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    for idx, value in enumerate([mean_d["R@1"], max_d["R@1"]]):
        ax.text(idx * width + x[0] - width / 2, value + 1.2, f"{value:.1f}", ha="center", fontsize=8)

    # (c) Training scale and supervision quality.
    q500 = _load_json("stage2_viclip_safe_dev_q500_eval200_gpu_v1.json")
    q800 = _load_json("stage2_bootstrap_safe_dev_q800_eval200_v1.json")
    v35 = _load_json("stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json")
    q1500 = _load_json("stage3_highquality_selected_q1500_replay_v35_recipe_eval1kAq200_v1.json")
    labels = ["q500\nsafe_dev", "q800\nsafe_dev", "q500+对齐多视角\n1kA q200", "q1500筛选\n1kA q200"]
    r1 = [
        _metric(q500, "adapter", "R@1"),
        _metric(q800, "adapter", "R@1"),
        _metric(v35, "adapter", "R@1"),
        _metric(q1500, "adapter", "R@1"),
    ]
    r10 = [
        _metric(q500, "adapter", "R@10"),
        _metric(q800, "adapter", "R@10"),
        _metric(v35, "adapter", "R@10"),
        _metric(q1500, "adapter", "R@10"),
    ]
    ax = axes[2]
    xx = np.arange(len(labels))
    ax.plot(xx, r1, marker="o", color="#2F5597", linewidth=1.8, label="R@1")
    ax.plot(xx, r10, marker="s", color="#A23B22", linewidth=1.5, label="R@10")
    ax.set_title("(c) 训练规模与监督质量", fontsize=11)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(35, 78)
    ax.set_ylabel("Recall (%)")
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.annotate(
        "继续扩大样本\n未稳定提升 R@1",
        xy=(3, r1[3]),
        xytext=(2.2, 57),
        arrowprops=dict(arrowstyle="->", linewidth=0.9, color="#111827"),
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#6B7280", lw=0.7),
    )

    for ax in axes:
        ax.set_axisbelow(True)

    fig.text(0.5, 0.01, "图3-4 关键实验设置选择的消融分析", ha="center", fontsize=12)
    fig.tight_layout(rect=(0.01, 0.06, 0.99, 0.98))
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "paper_fig3_setting_ablations.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "paper_fig3_setting_ablations.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
