from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "figures"
OUT_PNG = OUT_DIR / "paper_fig3_dual_encoder_retrieval.png"


def _set_chinese_font() -> None:
    font_candidates = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simsun.ttf",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for font_path in font_candidates:
        path = Path(font_path)
        if path.exists():
            mpl.font_manager.fontManager.addfont(str(path))
            font_name = mpl.font_manager.FontProperties(fname=str(path)).get_name()
            mpl.rcParams["font.family"] = font_name
            break
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42


def _box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    face: str,
    font_size: float = 10.2,
) -> None:
    rect = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.055",
        linewidth=1.25,
        edgecolor="#2E5E88",
        facecolor=face,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=font_size,
        color="#202020",
        linespacing=1.28,
    )


def _arrow(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float) -> None:
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="->",
        mutation_scale=13,
        linewidth=1.15,
        color="#303030",
        shrinkA=3,
        shrinkB=3,
    )
    ax.add_patch(arrow)


def main() -> None:
    _set_chinese_font()
    fig, ax = plt.subplots(figsize=(9.8, 4.05), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 9.8)
    ax.set_ylim(0, 4.05)
    ax.axis("off")

    stage_titles = [
        (1.15, "输入"),
        (3.48, "编码"),
        (5.85, "相似度"),
        (8.42, "排序"),
    ]
    for x, title in stage_titles:
        ax.text(
            x,
            3.75,
            title,
            ha="center",
            va="center",
            fontsize=11.0,
            fontweight="bold",
            color="#202020",
        )

    for x in [2.28, 4.72, 6.98]:
        ax.plot([x, x], [0.62, 3.55], color="#B0B0B0", lw=0.95, linestyle=(0, (3, 3)))

    _box(ax, 0.38, 2.42, 1.55, 0.78, "自然语言\n查询", "#F3F7FA")
    _box(ax, 0.38, 1.04, 1.55, 0.78, "候选视频\n集合", "#F3F7FA")
    _box(ax, 2.62, 2.42, 1.68, 0.78, "文本编码器", "#FBF7E8")
    _box(ax, 2.62, 1.04, 1.68, 0.78, "视频编码器", "#FBF7E8")
    _box(ax, 5.04, 1.70, 1.78, 0.92, "相似度\n计算", "#F2F8F1")

    ranking = FancyBboxPatch(
        (7.55, 0.78),
        1.85,
        2.58,
        boxstyle="round,pad=0.02,rounding_size=0.055",
        linewidth=1.25,
        edgecolor="#2E5E88",
        facecolor="#FBF3EF",
    )
    ax.add_patch(ranking)
    ax.text(8.48, 3.03, "候选视频排序", ha="center", va="center", fontsize=10.2, color="#202020")
    ax.text(
        8.48,
        2.48,
        "1. 视频 A\n2. 视频 B\n3. 视频 C\n   ……",
        ha="center",
        va="top",
        fontsize=9.8,
        color="#202020",
        linespacing=1.45,
    )

    _arrow(ax, 1.93, 2.81, 2.62, 2.81)
    _arrow(ax, 1.93, 1.43, 2.62, 1.43)
    _arrow(ax, 4.30, 2.81, 5.04, 2.22)
    _arrow(ax, 4.30, 1.43, 5.04, 2.08)
    _arrow(ax, 6.82, 2.16, 7.55, 2.16)

    ax.text(
        4.9,
        0.38,
        "文本与视频分别编码到统一语义空间，再通过相似度排序完成候选召回。",
        ha="center",
        va="center",
        fontsize=9.1,
        color="#555555",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
