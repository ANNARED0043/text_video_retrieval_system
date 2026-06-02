"""Draw a thesis figure for successful retrieval rank coverage."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "outputs" / "tables" / "analysis"
FIGURE_DIR = ROOT / "outputs" / "figures"


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def main() -> None:
    _setup_style()
    data = json.loads(
        (ANALYSIS_DIR / "failure_diagnosis_v35_1kA_q200.json").read_text(
            encoding="utf-8"
        )
    )
    buckets = data["rank_buckets"]
    top1 = buckets.get("top1", 0)
    top2_5 = buckets.get("top2_5", 0)
    top6_10 = buckets.get("top6_10", 0)
    top11_30 = buckets.get("top11_30", 0)
    outside = buckets.get("gt_outside_top30", 0)
    total = sum(buckets.values())

    values = [top1, top2_5, top6_10, top11_30, outside]
    labels = [
        f"Top-1\n{top1} ({top1 / total * 100:.1f}%)",
        f"Top-2~5\n{top2_5} ({top2_5 / total * 100:.1f}%)",
        f"Top-6~10\n{top6_10} ({top6_10 / total * 100:.1f}%)",
        f"Top-11~30\n{top11_30} ({top11_30 / total * 100:.1f}%)",
        f">Top-30\n{outside} ({outside / total * 100:.1f}%)",
    ]
    colors = ["#4C78A8", "#59A14F", "#F2CF5B", "#F58518", "#C44E52"]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    wedges, _ = ax.pie(
        values,
        startangle=92,
        colors=colors,
        wedgeprops={"width": 0.34, "edgecolor": "white", "linewidth": 1.5},
    )

    inner_values = [top1, total - top1]
    inner_colors = ["#2F5F9E", "#E8E8E8"]
    ax.pie(
        inner_values,
        radius=0.62,
        startangle=92,
        colors=inner_colors,
        wedgeprops={"width": 0.22, "edgecolor": "white", "linewidth": 1.2},
    )

    ax.text(
        0,
        0.03,
        f"Top-1\n{top1 / total * 100:.1f}%",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="#2F5F9E",
    )
    ax.text(
        0,
        -0.18,
        "successful\nfirst-rank cases",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#555555",
    )

    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        title="GT rank bucket",
    )
    ax.annotate(
        "Representative Top-1 case\nclear subject + action + object\nlocal evidence matches query",
        xy=(-0.25, 0.78),
        xytext=(-1.7, 1.15),
        arrowprops={
            "arrowstyle": "->",
            "color": "#333333",
            "lw": 1.2,
            "connectionstyle": "arc3,rad=-0.15",
        },
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "#2F5F9E",
            "linewidth": 1.0,
        },
        fontsize=9,
    )
    ax.set_title("Rank Coverage of the Best Alignment+Multiview Model", pad=14)
    ax.set(aspect="equal")
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURE_DIR / "paper_fig5_success_rank_coverage_bubble.png"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] wrote figure: {out}")


if __name__ == "__main__":
    main()
