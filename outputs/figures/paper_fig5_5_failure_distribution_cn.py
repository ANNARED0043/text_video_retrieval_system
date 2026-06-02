from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "outputs" / "tables" / "analysis" / "failure_diagnosis_v35_1kA_q200.json"
OUT_DIR = PROJECT_ROOT / "outputs" / "figures"
OUT_PNG = OUT_DIR / "paper_fig5_5_failure_distribution.png"
OUT_PDF = OUT_DIR / "paper_fig5_5_failure_distribution.pdf"


LABEL_MAP = {
    "object": "对象",
    "relation": "关系",
    "person_attribute": "人物属性",
    "action": "动作",
    "scene": "场景",
    "other": "其他",
    "multi_action": "多动作",
    "temporal_order": "时序顺序",
}


def _set_chinese_font() -> None:
    font_candidates = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simsun.ttf",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for font_path in font_candidates:
        if Path(font_path).exists():
            mpl.font_manager.fontManager.addfont(font_path)
            font_name = mpl.font_manager.FontProperties(fname=font_path).get_name()
            mpl.rcParams["font.family"] = font_name
            break
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42


def _load_counts() -> tuple[list[str], list[int]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    counts = payload.get("failure_tag_counts", {})
    ordered = sorted(counts.items(), key=lambda item: int(item[1]), reverse=True)
    labels = [LABEL_MAP.get(key, key) for key, _ in ordered]
    values = [int(value) for _, value in ordered]
    return labels, values


def main() -> None:
    _set_chinese_font()
    labels, values = _load_counts()
    total = sum(values)
    percentages = [value / total * 100 for value in values]

    colors = [
        "#8C2D2D",
        "#B75D4A",
        "#D68A6A",
        "#E7B08B",
        "#D6D2C4",
        "#B8C2B1",
        "#8FA99A",
        "#6F8F83",
    ]

    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.barh(
        y,
        values,
        color=colors[: len(values)],
        edgecolor="#2F2F2F",
        linewidth=0.7,
        height=0.64,
    )

    ax.invert_yaxis()
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5)
    ax.set_xlabel("错误标签出现次数", fontsize=11)
    ax.set_title("失败样本语义错误类型分布", fontsize=13, pad=12, fontweight="bold")

    ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.35, color="#808080")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")
    ax.tick_params(axis="x", labelsize=9.5)

    max_value = max(values)
    ax.set_xlim(0, max_value * 1.22)
    for bar, count, pct in zip(bars, values, percentages):
        ax.text(
            count + max_value * 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{count} ({pct:.1f}%)",
            va="center",
            ha="left",
            fontsize=9.5,
            color="#333333",
        )

    note = "注：同一失败样本可能对应多个语义错误标签，因此各类次数为多标签统计。"
    fig.text(0.08, 0.035, note, fontsize=8.8, color="#555555")
    fig.tight_layout(rect=(0.06, 0.08, 0.98, 0.96))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")
    print(f"[OK] wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
