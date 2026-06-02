"""Draw query-aware fusion versus fixed-weight fusion comparison."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parent
OUT_PNG = OUT_DIR / "Figure3_query_aware_fusion_comparison.png"
OUT_PDF = OUT_DIR / "Figure3_query_aware_fusion_comparison.pdf"


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


def add_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    facecolor: str,
    edgecolor: str = "#385D73",
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.4,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=11,
        linespacing=1.35,
        color="#111111",
    )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = "#3A3A3A",
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="->",
        mutation_scale=13,
        linewidth=1.3,
        color=color,
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arrow)


def draw_mechanism(ax: plt.Axes) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("（c）查询感知融合的计算路径", fontsize=12, pad=8)

    add_box(ax, (0.25, 3.25), 1.65, 0.75, "输入查询\nq", "#FCF8F1")
    add_box(ax, (0.25, 1.10), 1.65, 0.75, "候选视频\nv", "#F3F8FC")
    add_box(ax, (2.55, 3.25), 2.10, 0.75, "查询语义复杂度\n动作/关系/属性", "#F7F4FB")
    add_box(ax, (2.55, 1.10), 2.10, 0.75, "全局表示与\n局部视角表示", "#F3FAF5")
    add_box(ax, (5.45, 2.15), 1.75, 0.75, "动态权重\nαq", "#FFF5F5")
    add_box(ax, (7.95, 2.15), 1.70, 0.75, "最终相似度\nSfinal", "#F3F8FC")

    add_arrow(ax, (1.90, 3.63), (2.55, 3.63))
    add_arrow(ax, (1.90, 1.48), (2.55, 1.48))
    add_arrow(ax, (4.65, 3.63), (5.45, 2.72))
    add_arrow(ax, (4.65, 1.48), (5.45, 2.32))
    add_arrow(ax, (7.20, 2.52), (7.95, 2.52))

    ax.text(
        5.0,
        0.28,
        r"$S_{\mathrm{final}}=(1-\alpha_q)S_{\mathrm{global}}+\alpha_q S_{\mathrm{local}}$",
        ha="center",
        va="center",
        fontsize=12,
        color="#222222",
    )


def main() -> None:
    setup_style()
    fig = plt.figure(figsize=(14.8, 6.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.08], wspace=0.28, hspace=0.42)

    ax_fixed = fig.add_subplot(gs[0, 0])
    ax_query = fig.add_subplot(gs[0, 1])
    ax_flow = fig.add_subplot(gs[1, :])

    query_types = ["简单场景", "单一对象", "动作约束", "关系约束", "人物属性"]
    x = np.arange(len(query_types))
    fixed_alpha = np.full(len(query_types), 0.20)
    aware_alpha = np.array([0.12, 0.18, 0.42, 0.50, 0.46])

    ax_fixed.plot(x, fixed_alpha, marker="o", color="#4C78A8", linewidth=2.0)
    ax_fixed.fill_between(x, fixed_alpha, 0, color="#4C78A8", alpha=0.10)
    ax_fixed.set_ylim(0, 0.62)
    ax_fixed.set_xticks(x)
    ax_fixed.set_xticklabels(query_types)
    ax_fixed.set_ylabel("局部视角权重 α")
    ax_fixed.set_title("（a）固定权重融合：所有查询使用同一权重", fontsize=12, pad=8)
    ax_fixed.grid(axis="y")
    ax_fixed.text(
        2,
        0.31,
        "无法区分查询复杂度",
        ha="center",
        va="center",
        fontsize=10.5,
        color="#555555",
    )

    colors = ["#8FB6D9", "#8FB6D9", "#E59A59", "#D96C75", "#D96C75"]
    ax_query.bar(x, aware_alpha, color=colors, width=0.58)
    ax_query.set_ylim(0, 0.62)
    ax_query.set_xticks(x)
    ax_query.set_xticklabels(query_types)
    ax_query.set_ylabel("局部视角权重 αq")
    ax_query.set_title("（b）查询感知融合：复杂查询提高局部证据权重", fontsize=12, pad=8)
    ax_query.grid(axis="y")
    for idx, val in enumerate(aware_alpha):
        ax_query.text(idx, val + 0.025, f"{val:.2f}", ha="center", fontsize=9.5)

    draw_mechanism(ax_flow)

    fig.suptitle("图3-X 固定权重融合与查询感知融合机制对比", fontsize=15, y=0.995)
    fig.text(
        0.5,
        0.015,
        "注：图中权重用于说明机制差异。实际系统根据查询语义复杂度、候选分差和局部证据需求动态调整融合强度。",
        ha="center",
        va="center",
        fontsize=10.5,
        color="#333333",
    )
    fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")
    print(f"[OK] wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
