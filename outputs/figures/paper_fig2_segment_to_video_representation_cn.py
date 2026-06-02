from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "figures"
OUT_PNG = OUT_DIR / "paper_fig2_segment_to_video_representation.png"


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
    edge: str = "#2E5E88",
    font_size: float = 10.0,
) -> None:
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.045",
        linewidth=1.25,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=font_size,
        color="#202020",
        linespacing=1.25,
    )


def _arrow(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float, color: str = "#303030") -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=12,
            linewidth=1.15,
            color=color,
            shrinkA=3,
            shrinkB=3,
        )
    )


def main() -> None:
    _set_chinese_font()
    fig, ax = plt.subplots(figsize=(9.8, 3.05), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 9.8)
    ax.set_ylim(0, 3.05)
    ax.axis("off")

    center_y = 1.52
    _box(ax, 0.42, center_y - 0.36, 1.2, 0.72, "原始视频", "#F3F7FA")
    _box(ax, 2.02, center_y - 0.36, 1.38, 0.72, "视频片段\n划分", "#FBF7E8")
    _box(ax, 5.42, center_y - 0.36, 1.48, 0.72, "视觉特征\n编码", "#F2F8F1")
    _box(ax, 7.34, center_y - 0.36, 1.42, 0.72, "均值 / 最大\n池化", "#F7F4FA")

    seg_x = 3.85
    seg_w = 1.12
    seg_h = 0.46
    seg_positions = [2.25, 1.52, 0.79]
    for idx, y in enumerate(seg_positions, start=1):
        _box(ax, seg_x, y - seg_h / 2, seg_w, seg_h, f"片段 {idx}", "#FFFFFF", font_size=9.4)

    _arrow(ax, 1.62, center_y, 2.02, center_y)
    _arrow(ax, 3.40, center_y, seg_x, seg_positions[0])
    _arrow(ax, 3.40, center_y, seg_x, seg_positions[1])
    _arrow(ax, 3.40, center_y, seg_x, seg_positions[2])
    _arrow(ax, seg_x + seg_w, seg_positions[0], 5.42, center_y + 0.20)
    _arrow(ax, seg_x + seg_w, seg_positions[1], 5.42, center_y)
    _arrow(ax, seg_x + seg_w, seg_positions[2], 5.42, center_y - 0.20)
    _arrow(ax, 6.90, center_y, 7.34, center_y)
    _arrow(ax, 8.76, center_y, 9.25, center_y, color="#8C2D2D")

    ax.text(
        9.28,
        center_y,
        "视频级\n表示",
        ha="left",
        va="center",
        fontsize=10.0,
        fontweight="bold",
        color="#8C2D2D",
        linespacing=1.25,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
