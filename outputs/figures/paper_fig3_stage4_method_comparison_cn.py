from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


OUT_DIR = Path(__file__).resolve().parent


def _setup_font() -> None:
    candidates = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = font_manager.FontProperties(
                fname=path
            ).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42


def _annotate_bars(ax, bars, dy: float = 0.35) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + dy,
            f"{height:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#222222",
        )


def main() -> None:
    _setup_font()
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.6), dpi=220)
    fig.patch.set_facecolor("white")

    # Panel A: controlled full-1kA progression in this project.
    stages = ["固定多视角", "查询感知\n+成对教师", "系统增强"]
    r1 = np.array([38.7, 39.1, 39.7])
    r5 = np.array([61.1, 61.6, 61.3])
    r10 = np.array([70.9, 72.1, 71.6])
    x = np.arange(len(stages))
    width = 0.23
    colors = ["#C84B4B", "#4B79A8", "#5A8F5A"]
    ax = axes[0]
    bars1 = ax.bar(x - width, r1, width, label="R@1", color=colors[0], alpha=0.88)
    ax.bar(x, r5, width, label="R@5", color=colors[1], alpha=0.88)
    ax.bar(x + width, r10, width, label="R@10", color=colors[2], alpha=0.88)
    _annotate_bars(ax, bars1, dy=0.45)
    ax.plot(x - width, r1, color="#6E1F1F", marker="o", linewidth=1.4)
    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=9)
    ax.set_ylim(34, 76)
    ax.set_ylabel("Recall (%)", fontsize=10)
    ax.set_title("（a）本文方法在 full 1kA 上的阶段性增益", fontsize=11, pad=10)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.annotate(
        "R@1: 38.7 → 39.7",
        xy=(2 - width, 39.7),
        xytext=(0.62, 45.5),
        arrowprops=dict(arrowstyle="->", color="#555555", lw=0.9),
        fontsize=9,
        color="#333333",
    )

    # Panel B: external positioning. Values are from public reports; settings differ.
    methods = ["BT-Adapter", "本文\nStage4", "CLIP4Clip", "X-Pool", "X-CoT\n+X-Pool"]
    ext_r1 = np.array([40.9, 39.7, 44.5, 46.9, 47.3])
    ax = axes[1]
    bar_colors = ["#9AA6B2", "#C84B4B", "#9AA6B2", "#9AA6B2", "#9AA6B2"]
    bars = ax.bar(np.arange(len(methods)), ext_r1, width=0.55, color=bar_colors, alpha=0.9)
    _annotate_bars(ax, bars, dy=0.35)
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels(methods, fontsize=9)
    ax.set_ylim(36, 49.5)
    ax.set_ylabel("R@1 (%)", fontsize=10)
    ax.set_title("（b）与近年相关方法的 R@1 定位", fontsize=11, pad=10)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        0.02,
        0.97,
        "注：公开方法训练规模与设置不同；本文强调轻量可部署条件下的受控增益。",
        transform=ax.transAxes,
        fontsize=8,
        va="top",
        ha="left",
        color="#555555",
    )

    fig.tight_layout(w_pad=2.0)
    out = OUT_DIR / "paper_fig3_stage4_method_comparison_cn.png"
    fig.savefig(out, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()

