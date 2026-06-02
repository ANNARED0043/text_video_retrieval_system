from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "figures"
OUT_PNG = OUT_DIR / "paper_fig3_layered_method_pipeline.png"


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


def _draw_card(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    items: list[str],
    face: str,
    highlight: bool = False,
) -> None:
    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.12",
        linewidth=2.25 if highlight else 1.35,
        edgecolor="#8C2D2D" if highlight else "#2E2E2E",
        facecolor=face,
    )
    ax.add_patch(card)
    ax.text(
        x + w / 2,
        y + h - 0.25,
        title,
        ha="center",
        va="top",
        fontsize=10.8 if highlight else 10.6,
        fontweight="bold",
        color="#8C2D2D" if highlight else "#202020",
    )
    ax.plot([x + 0.18, x + w - 0.18], [y + h - 0.58, y + h - 0.58], color="#3F3F3F", lw=0.9)

    item_y = y + h - 0.92
    for item in items:
        ax.text(x + 0.25, item_y, f"• {item}", ha="left", va="top", fontsize=10.2, color="#202020")
        item_y -= 0.34


def _draw_arrow(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float) -> None:
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="->",
        mutation_scale=16,
        linewidth=1.35,
        color="#2E2E2E",
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arrow)


def main() -> None:
    _set_chinese_font()
    fig, ax = plt.subplots(figsize=(10.8, 3.75), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 10.8)
    ax.set_ylim(0, 3.75)
    ax.axis("off")

    cards = [
        (
            "基础召回层",
            ["视频切片", "特征提取", "FAISS召回"],
            "#F3F7FA",
        ),
        (
            "选择性查询改写",
            ["歧义检测", "LLM改写", "改写缓存"],
            "#FBF7E8",
        ),
        (
            "候选结果优化",
            ["Top-K候选", "语义重评分", "融合排序"],
            "#F2F8F1",
        ),
        (
            "细粒度表征增强",
            ["对齐教师", "多视角特征", "局部对齐"],
        "#FFF1EC",
        ),
        (
            "错误学习闭环",
            ["失败诊断", "反馈教师", "门控晋升"],
            "#FBF3EF",
        ),
    ]

    x0 = 0.35
    y0 = 0.72
    w = 1.65
    h = 2.45
    gap = 0.45
    xs = []
    for idx, (title, items, face) in enumerate(cards):
        x = x0 + idx * (w + gap)
        xs.append(x)
        _draw_card(ax, x, y0, w, h, title, items, face, highlight=(idx == 3))
        if idx > 0:
            _draw_arrow(ax, xs[idx - 1] + w + 0.03, y0 + h / 2, x - 0.03, y0 + h / 2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
