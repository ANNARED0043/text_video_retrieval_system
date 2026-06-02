"""Draw a quick mean/max pooling comparison figure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "outputs" / "tables" / "analysis"
FIGURE_DIR = ROOT / "outputs" / "figures"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _metrics(payload: dict[str, Any]) -> dict[str, float]:
    return payload.get("metrics", payload)


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


def main() -> None:
    _setup_style()
    mean_payload = _load(ANALYSIS_DIR / "pooling_smoke200_mean_topk200.json")
    max_payload = _load(ANALYSIS_DIR / "pooling_smoke200_max_topk200.json")
    mean = _metrics(mean_payload)
    max_ = _metrics(max_payload)

    recall_metrics = ["R@1", "R@5", "R@10"]
    stability_metrics = ["MedR", "MnR"]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9), gridspec_kw={"width_ratios": [1.25, 1.0]})

    x = np.arange(len(recall_metrics))
    width = 0.34
    mean_vals = [float(mean[m]) for m in recall_metrics]
    max_vals = [float(max_[m]) for m in recall_metrics]
    bars_a = axes[0].bar(x - width / 2, mean_vals, width, label="Mean pooling", color="#4C78A8")
    bars_b = axes[0].bar(x + width / 2, max_vals, width, label="Max pooling", color="#C44E52")
    axes[0].set_xticks(x, recall_metrics)
    axes[0].set_ylabel("Recall (%)")
    axes[0].set_title("(a) Retrieval recall")
    axes[0].set_ylim(0, max(mean_vals + max_vals) * 1.22)
    axes[0].bar_label(bars_a, fmt="%.1f", padding=2, fontsize=8)
    axes[0].bar_label(bars_b, fmt="%.1f", padding=2, fontsize=8)
    axes[0].legend(loc="upper left")

    x2 = np.arange(len(stability_metrics))
    mean_stability = [float(mean[m]) for m in stability_metrics]
    max_stability = [float(max_[m]) for m in stability_metrics]
    bars_c = axes[1].bar(x2 - width / 2, mean_stability, width, label="Mean pooling", color="#4C78A8")
    bars_d = axes[1].bar(x2 + width / 2, max_stability, width, label="Max pooling", color="#C44E52")
    axes[1].set_xticks(x2, stability_metrics)
    axes[1].set_ylabel("Rank (lower is better)")
    axes[1].set_title("(b) Rank stability")
    axes[1].set_ylim(0, max(mean_stability + max_stability) * 1.22)
    axes[1].bar_label(bars_c, fmt="%.1f", padding=2, fontsize=8)
    axes[1].bar_label(bars_d, fmt="%.1f", padding=2, fontsize=8)

    n = int(mean.get("N", mean_payload.get("queries_planned", 0)))
    fig.suptitle(f"Mean vs. Max Pooling on 1kA Smoke Subset (N={n})", y=1.03, fontsize=13)
    fig.subplots_adjust(wspace=0.32, top=0.78)

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURE_DIR / "paper_fig5_pooling_mean_max_smoke200.png"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] wrote figure: {out}")


if __name__ == "__main__":
    main()
