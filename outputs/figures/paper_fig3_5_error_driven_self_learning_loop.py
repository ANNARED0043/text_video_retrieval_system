"""Draw Figure 3-5: error-driven self-learning loop."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import (
    Circle,
    FancyArrowPatch,
    FancyBboxPatch,
    Rectangle,
)


OUT_DIR = Path(__file__).resolve().parent
OUT_PNG = OUT_DIR / "Figure3_5_error_driven_self_learning_loop.png"
OUT_PDF = OUT_DIR / "Figure3_5_error_driven_self_learning_loop.pdf"


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


def add_panel(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    subtitle: str,
    edgecolor: str,
    facecolor: str,
) -> None:
    panel = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.03,rounding_size=0.08",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.35,
    )
    ax.add_patch(panel)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height - 0.34,
        title,
        ha="center",
        va="top",
        fontsize=11.5,
        color="#111111",
    )
    ax.text(
        xy[0] + width / 2,
        xy[1] + height - 0.68,
        subtitle,
        ha="center",
        va="top",
        fontsize=8.6,
        color="#555555",
    )


def add_inner_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    edgecolor: str,
    facecolor: str = "#FFFFFF",
    fontsize: float = 8.8,
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0.75,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#222222",
        linespacing=1.28,
    )


def add_text(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    fontsize: float = 8.6,
    color: str = "#333333",
    ha: str = "center",
) -> None:
    ax.text(x, y, text, ha=ha, va="center", fontsize=fontsize, color=color, linespacing=1.25)


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = "#4A4A4A",
    rad: float = 0.0,
    lw: float = 1.25,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arrow)


def draw_log_icon(ax: plt.Axes, x: float, y: float) -> None:
    for idx, length in enumerate([0.55, 0.42, 0.50]):
        ax.text(x, y - idx * 0.12, f"{idx + 1}", fontsize=7.2, va="center")
        ax.add_patch(
            Rectangle(
                (x + 0.18, y - idx * 0.12 - 0.03),
                length,
                0.055,
                facecolor="#8FA7BA",
                edgecolor="#8FA7BA",
            )
        )


def draw_rank_bars(ax: plt.Axes, x: float, y: float) -> None:
    heights = [0.16, 0.28, 0.43, 0.24]
    for idx, hgt in enumerate(heights):
        ax.add_patch(
            Rectangle(
                (x + idx * 0.16, y),
                0.08,
                hgt,
                facecolor="#7A9A73",
                edgecolor="#7A9A73",
            )
        )
    ax.plot([x - 0.04, x + 0.65], [y, y], color="#7A9A73", lw=0.8)


def draw_teacher_icon(ax: plt.Axes, x: float, y: float) -> None:
    ax.add_patch(Circle((x, y + 0.25), 0.07, facecolor="#8C6A85", edgecolor="#8C6A85"))
    ax.add_patch(Rectangle((x - 0.08, y + 0.05), 0.16, 0.13, facecolor="#8C6A85", edgecolor="#8C6A85"))
    ax.plot([x + 0.12, x + 0.35], [y + 0.14, y + 0.28], color="#8C6A85", lw=1.4)
    ax.plot([x + 0.35, x + 0.55], [y + 0.28, y + 0.28], color="#8C6A85", lw=1.4)
    ax.plot([x + 0.55, x + 0.55], [y + 0.28, y + 0.02], color="#8C6A85", lw=1.4)
    ax.plot([x + 0.55, x + 0.18], [y + 0.02, y + 0.02], color="#8C6A85", lw=1.4)


def draw_gate_icon(ax: plt.Axes, x: float, y: float) -> None:
    ax.plot([x, x + 0.25, x + 0.5, x + 0.5, x + 0.25, x, x],
            [y + 0.18, y + 0.34, y + 0.18, y - 0.16, y - 0.34, y - 0.16, y + 0.18],
            color="#B15A5A", lw=1.3)
    for idx in range(3):
        ax.plot([x + 0.13 + idx * 0.12, x + 0.13 + idx * 0.12],
                [y - 0.18, y + 0.13], color="#B15A5A", lw=1.0)
    ax.plot([x + 0.08, x + 0.42], [y - 0.03, y - 0.03], color="#B15A5A", lw=1.0)


def draw_model_icon(ax: plt.Axes, x: float, y: float, color: str, lock: bool = False) -> None:
    ax.add_patch(Circle((x, y), 0.22, facecolor=color, edgecolor=color, alpha=0.88))
    if lock:
        ax.add_patch(Rectangle((x - 0.09, y - 0.09), 0.18, 0.14, facecolor="white", edgecolor="white"))
        ax.add_patch(Circle((x, y + 0.05), 0.075, facecolor="none", edgecolor="white", lw=1.6))
    else:
        ax.text(x, y - 0.01, "优", ha="center", va="center", fontsize=12, color="white")


def main() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(17.2, 7.4))
    ax.set_xlim(0, 17.0)
    ax.set_ylim(0, 7.4)
    ax.axis("off")

    ax.text(
        8.5,
        6.92,
        "图3-5 错误驱动自学习闭环方法",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#111111",
    )

    panels = [
        ((0.45, 2.30), 1.95, 3.15, "检索结果与日志", "日志输入", "#486F95", "#F7FBFF"),
        ((2.85, 2.30), 1.95, 3.15, "失败样本诊断", "错误分析", "#5E8757", "#F8FCF7"),
        ((5.25, 2.30), 2.05, 3.15, "高价值错误筛选", "近错样本挖掘", "#C17632", "#FFF9F2"),
        ((7.95, 2.62), 1.85, 2.52, "反馈教师", "监督信号构建", "#8B5A80", "#FCF8FC"),
        ((10.35, 2.62), 1.75, 2.52, "候选模型", "候选更新", "#8B5A80", "#FCF8FC"),
        ((12.55, 2.62), 1.55, 2.52, "验证门控", "安全验证", "#B15A5A", "#FFF7F7"),
    ]
    for panel in panels:
        add_panel(ax, *panel)

    add_inner_box(ax, (0.72, 4.22), 1.40, 0.46, "排名日志", "#A8BBD0")
    add_inner_box(ax, (0.72, 3.50), 1.40, 0.46, "失败样本", "#A8BBD0")
    add_inner_box(ax, (0.72, 2.78), 1.40, 0.46, "用户反馈", "#A8BBD0")

    add_inner_box(ax, (3.12, 4.21), 1.40, 0.44, "排名分析", "#B8CBB4")
    add_inner_box(ax, (3.12, 3.55), 1.40, 0.44, "错误类型", "#B8CBB4")
    add_inner_box(ax, (3.12, 2.89), 1.40, 0.44, "不确定性", "#B8CBB4")
    add_inner_box(ax, (3.12, 2.42), 1.40, 0.25, r"$1<r(q)\leq K_f$", "#B8CBB4", fontsize=8.2)

    ax.text(5.48, 4.47, "1", fontsize=8.4)
    ax.add_patch(Rectangle((5.78, 4.39), 0.38, 0.12, facecolor="#D6D6D6", edgecolor="#D6D6D6"))
    ax.text(6.28, 4.43, "通过", fontsize=8.2, color="#5E8757", va="center")
    for idx, num in enumerate(["2", "3", "...", "30", "31", "...", "K"]):
        y = 4.02 - idx * 0.28
        ax.text(5.48, y, num, fontsize=8.4)
        color = "#F2B98E" if num in {"2", "3", "30"} else "#D6D6D6"
        ax.add_patch(Rectangle((5.78, y - 0.05), 0.38, 0.12, facecolor=color, edgecolor=color))
    ax.text(6.38, 3.62, "近错样本", fontsize=8.6, color="#A95B22")
    add_inner_box(ax, (5.64, 2.52), 1.05, 0.34, "rank 2-30", "#D59A62", "#FFFDFB", 8.4)

    draw_teacher_icon(ax, 8.47, 3.92)
    add_inner_box(ax, (8.17, 3.28), 1.30, 0.36, "软监督", "#C8AFC3", "#FFFFFF")
    add_inner_box(ax, (8.17, 2.80), 1.30, 0.36, "局部纠正", "#C8AFC3", "#FFFFFF")

    add_inner_box(ax, (10.58, 3.86), 1.30, 0.50, "当前最优\n热启动", "#C8AFC3", fontsize=8.4)
    add_inner_box(ax, (10.58, 3.12), 1.30, 0.50, "候选模型\n参数更新", "#C8AFC3", fontsize=8.4)

    draw_gate_icon(ax, 13.05, 4.12)
    for idx, text in enumerate(["性能提升", "稳定性", "风险控制"]):
        y = 3.42 - idx * 0.36
        ax.text(12.82, y, text, color="#333333", fontsize=8.2, va="center")

    add_panel(ax, (15.05, 3.82), 1.18, 0.95, "当前模型", "晋升后启用", "#C75D5D", "#FFF8F8")
    add_panel(ax, (15.05, 2.22), 1.18, 0.95, "保留旧模型", "拒绝后回退", "#C75D5D", "#FFF8F8")

    add_arrow(ax, (2.40, 3.88), (2.85, 3.88), "#486F95")
    add_arrow(ax, (4.80, 3.88), (5.25, 3.88), "#5E8757")
    add_arrow(ax, (7.30, 3.88), (7.95, 3.88), "#C17632")
    add_arrow(ax, (9.80, 3.88), (10.35, 3.88), "#8B5A80")
    add_arrow(ax, (12.10, 3.88), (12.55, 3.88), "#8B5A80")
    add_arrow(ax, (14.10, 3.86), (15.05, 4.22), "#B15A5A")
    add_arrow(ax, (14.10, 3.30), (15.05, 2.70), "#B15A5A")
    ax.text(14.50, 4.38, "晋升", fontsize=8.8, color="#7A2C2C")
    ax.text(14.50, 2.86, "拒绝", fontsize=8.8, color="#7A2C2C")

    add_arrow(ax, (15.64, 4.77), (0.85, 5.55), "#486F95", rad=0.05, lw=1.1)
    add_arrow(ax, (0.85, 5.55), (0.85, 5.45), "#486F95", lw=1.1)

    ax.text(
        8.5,
        0.88,
        "说明：闭环以失败样本为起点，通过近错样本筛选构建反馈教师；"
        "候选模型仅在安全验证集通过后晋升，否则保留当前模型。",
        ha="center",
        va="center",
        fontsize=10.2,
        color="#333333",
    )
    ax.text(
        8.5,
        0.50,
        "该机制用于探索持续学习可行性，当前作为扩展模块，不替代对齐教师与多视角特征的主结果。",
        ha="center",
        va="center",
        fontsize=9.8,
        color="#666666",
    )

    fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")
    print(f"[OK] wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
