"""Draw latency and token-cost comparison for system testing."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "figures"
OUT_PNG = OUT_DIR / "paper_fig5_latency_cost_comparison.png"
OUT_PDF = OUT_DIR / "paper_fig5_latency_cost_comparison.pdf"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "font.family": "sans-serif",
            "font.sans-serif": [
                "SimSun",
                "Songti SC",
                "Microsoft YaHei",
                "SimHei",
                "Noto Sans CJK SC",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "axes.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_json(relative: str) -> dict:
    path = PROJECT_ROOT / relative
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    setup_style()
    baseline = load_json("outputs/tables/analysis/baseline_vith14_mean_topk200_q200.json")
    rewrite = load_json(
        "outputs/tables/final_rewrite_selective_hybrid_mean_topk200_thr0.25_ba0.8_summary.json"
    )
    rerank = load_json(
        "outputs/tables/week7_rewrite_selective_mean_topk200_rerank5_alpha0.8_thr0.2_summary.json"
    )

    names = ["Baseline", "Selective Rewrite", "Rewrite + Rerank"]
    cn_names = ["Baseline", "选择性改写", "改写+重排序"]
    latency_ms = [
        float(baseline["latency"]["total_ms"]["avg"]),
        float(rewrite["avg_search_ms"]),
        float(rerank["latency"]["avg_total_ms"]),
    ]
    latency_breakdown = {
        "检索/召回": [
            float(baseline["latency"]["search_ms"]["avg"]),
            float(rewrite["avg_search_ms"]),
            float(rerank["latency"]["avg_search_ms"]),
        ],
        "候选语义构建": [0.0, 0.0, float(rerank["latency"]["avg_candidate_semantics_ms"])],
        "LLM重排序": [0.0, 0.0, float(rerank["latency"]["avg_rerank_ms"])],
    }
    token_total = [
        0,
        int(rewrite["tokens"]["total"]),
        int(rerank["token_usage"]["total_tokens"]),
    ]
    token_per_query = [
        0.0,
        token_total[1] / float(rewrite["queries_evaluated"]),
        token_total[2] / float(rerank["N"]),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.2))
    colors = ["#4C78A8", "#72B7B2", "#F58518"]
    x = np.arange(len(names))

    bottom = np.zeros(len(names))
    breakdown_colors = ["#4C78A8", "#72B7B2", "#F58518"]
    for idx, (label, values) in enumerate(latency_breakdown.items()):
        axes[0].bar(
            x,
            values,
            bottom=bottom,
            width=0.55,
            label=label,
            color=breakdown_colors[idx],
            edgecolor="black",
            linewidth=0.35,
        )
        bottom += np.array(values)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("平均响应时间（ms，对数刻度）")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(cn_names)
    axes[0].set_title("（a）在线响应时间对比", pad=12)
    axes[0].grid(axis="y")
    axes[0].legend(loc="upper left", fontsize=8.5)
    for idx, value in enumerate(latency_ms):
        axes[0].text(idx, value * 1.15, f"{value:.1f} ms", ha="center", fontsize=8.8)

    axes[1].bar(
        x,
        token_per_query,
        width=0.55,
        color=colors,
        edgecolor="black",
        linewidth=0.45,
    )
    axes[1].set_ylabel("平均 Token 消耗（tokens/query）")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(cn_names)
    axes[1].set_title("（b）LLM 调用成本对比", pad=12)
    axes[1].grid(axis="y")
    for idx, value in enumerate(token_per_query):
        label = "0" if value == 0 else f"{value:.0f}"
        axes[1].text(idx, value + max(token_per_query) * 0.035, label, ha="center", fontsize=8.8)

    fig.suptitle("图5-X 不同检索路径的响应时间与调用成本对比", fontsize=14, y=1.02)
    fig.text(
        0.5,
        -0.02,
        "注：实验基于 MSR-VTT 1kA q200。Baseline 不调用大语言模型；Rewrite 与 Rerank 的成本主要来自 LLM 调用与候选语义比较。",
        ha="center",
        va="center",
        fontsize=9.5,
        color="#333333",
    )
    fig.tight_layout()
    fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")
    print(f"[OK] wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
