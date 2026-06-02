"""Draw Figure 3-2: selective query rewrite pipeline in Chinese."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parent
OUT_PNG = OUT_DIR / "Figure3_2_rewrite_pipeline.png"
OUT_PDF = OUT_DIR / "Figure3_2_rewrite_pipeline.pdf"


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
    facecolor: str = "#F7F7F7",
    edgecolor: str = "#34495E",
    linewidth: float = 1.5,
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=12,
        color="#111111",
        linespacing=1.35,
    )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str | None = None,
    label_offset: tuple[float, float] = (0.0, 0.0),
    color: str = "#3A3A3A",
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="->",
        mutation_scale=14,
        linewidth=1.5,
        color=color,
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arrow)
    if label:
        ax.text(
            (start[0] + end[0]) / 2 + label_offset[0],
            (start[1] + end[1]) / 2 + label_offset[1],
            label,
            ha="center",
            va="center",
            fontsize=11,
            color="#8B1A1A",
        )


def main() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(14.5, 5.1))
    ax.set_xlim(0, 14.5)
    ax.set_ylim(0, 5.1)
    ax.axis("off")

    border = "#2F5D78"
    add_box(ax, (0.45, 2.2), 1.75, 0.78, "原始查询", "#FCF8F1", border)
    add_box(ax, (2.75, 2.2), 2.15, 0.78, "歧义评分\n与触发判断", "#F3F8FC", border)
    add_box(ax, (5.45, 2.2), 2.25, 0.78, "阈值决策", "#FCF8F1", border)
    add_box(ax, (8.35, 3.42), 2.2, 0.78, "调用大语言模型\n生成改写查询", "#F3FAF5", border)
    add_box(ax, (8.35, 1.02), 2.2, 0.78, "保持原查询\n直接透传", "#F8F4FB", border)
    add_box(ax, (11.55, 2.25), 1.9, 0.78, "改写缓存", "#FFF5F5", border)
    add_box(ax, (11.55, 0.62), 1.9, 0.78, "文本检索", "#F3F8FC", border)

    add_arrow(ax, (2.2, 2.59), (2.75, 2.59))
    add_arrow(ax, (4.9, 2.59), (5.45, 2.59))
    add_arrow(ax, (7.7, 2.59), (8.35, 3.82), "是", (-0.24, 0.2))
    add_arrow(ax, (7.7, 2.59), (8.35, 1.42), "否", (-0.24, -0.2))
    add_arrow(ax, (10.55, 3.81), (11.55, 2.66))
    add_arrow(ax, (10.55, 1.41), (11.55, 1.02))
    add_arrow(ax, (12.5, 2.25), (12.5, 1.4))

    ax.text(
        7.25,
        4.72,
        "图3-2 选择性查询改写流程",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#111111",
    )
    ax.text(
        7.25,
        0.17,
        "说明：系统仅在查询存在语义含混、约束不足或候选分差较小时触发改写；"
        "语义已清晰的查询直接进入文本检索，以降低语义漂移与调用成本。",
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
