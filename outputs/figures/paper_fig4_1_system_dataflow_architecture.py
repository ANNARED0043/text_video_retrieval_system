"""Draw Figure 4-1: system architecture and data flow in Chinese."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parent
OUT_PNG = OUT_DIR / "Figure4-1_system_module_architecture.png"
OUT_PDF = OUT_DIR / "Figure4-1_system_module_architecture.pdf"


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


def add_layer(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    facecolor: str,
    edgecolor: str,
) -> None:
    layer = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.08",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.0,
    )
    ax.add_patch(layer)
    ax.text(
        xy[0] + 0.22,
        xy[1] + height - 0.16,
        title,
        ha="left",
        va="top",
        fontsize=11.4,
        fontweight="bold",
        color=edgecolor,
    )


def add_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    desc: str,
    edgecolor: str,
    facecolor: str = "#FFFFFF",
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.055",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.25,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height * 0.62,
        title,
        ha="center",
        va="center",
        fontsize=10.8,
        color="#111111",
    )
    if desc:
        ax.text(
            xy[0] + width / 2,
            xy[1] + height * 0.30,
            desc,
            ha="center",
            va="center",
            fontsize=8.6,
            color="#555555",
            linespacing=1.25,
        )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = "#4A4A4A",
    rad: float = 0.0,
    lw: float = 1.2,
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


def add_note(ax: plt.Axes, x: float, y: float, text: str, color: str) -> None:
    ax.text(x, y, text, ha="center", va="center", fontsize=8.6, color=color)


def main() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(16.4, 8.45))
    ax.set_xlim(0, 16.2)
    ax.set_ylim(0, 8.45)
    ax.axis("off")

    ax.text(
        8.1,
        8.02,
        "图4-1 系统模块架构与数据流",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#111111",
    )

    add_layer(ax, (0.45, 5.85), 15.30, 1.35, "离线视频处理与索引构建层", "#F7FBFF", "#486F95")
    add_layer(ax, (0.45, 4.02), 15.30, 1.35, "在线文本检索与结果输出层", "#FFFFFF", "#555555")
    add_layer(ax, (0.45, 2.18), 15.30, 1.35, "表征增强与反馈学习层", "#F7F5FC", "#805A86")
    add_layer(ax, (0.45, 0.82), 15.30, 1.05, "前端交互与实验管理层", "#FAFAFA", "#6B7280")

    # Offline layer.
    y_off = 6.10
    add_box(ax, (0.95, y_off), 1.45, 0.65, "原始视频", "视频文件", "#486F95", "#FFFFFF")
    add_box(ax, (3.00, y_off), 1.65, 0.65, "清单构建", "manifest / query", "#486F95", "#FFFFFF")
    add_box(ax, (5.35, y_off), 1.80, 0.65, "片段级编码", "视频片段特征", "#486F95", "#FFFFFF")
    add_box(ax, (7.95, y_off), 1.70, 0.65, "视频级聚合", "mean pooling", "#486F95", "#FFFFFF")
    add_box(ax, (10.45, y_off), 1.70, 0.65, "向量索引", "FAISS", "#486F95", "#FFFFFF")
    add_box(ax, (13.00, y_off), 1.95, 0.65, "离线结果管理", "summary / 图表", "#486F95", "#FFFFFF")

    for start, end in [
        ((2.40, 6.43), (3.00, 6.43)),
        ((4.65, 6.43), (5.35, 6.43)),
        ((7.15, 6.43), (7.95, 6.43)),
        ((9.65, 6.43), (10.45, 6.43)),
        ((12.15, 6.43), (13.00, 6.43)),
    ]:
        add_arrow(ax, start, end, "#486F95")

    # Online layer.
    y_on = 4.27
    add_box(ax, (0.95, y_on), 1.45, 0.65, "文本查询", "用户输入", "#555555")
    add_box(ax, (3.00, y_on), 1.65, 0.65, "选择性改写", "歧义检测 / 缓存", "#777777")
    add_box(ax, (5.35, y_on), 1.80, 0.65, "基础召回", "Top-K 候选", "#555555")
    add_box(ax, (7.95, y_on), 1.70, 0.65, "候选优化", "rerank / 聚合", "#777777")
    add_box(ax, (10.45, y_on), 1.70, 0.65, "结果组织", "Top-5 / GT rank", "#555555")
    add_box(ax, (13.00, y_on), 1.95, 0.65, "检索输出", "视频播放 / 反馈", "#555555")

    for start, end in [
        ((2.40, 4.60), (3.00, 4.60)),
        ((4.65, 4.60), (5.35, 4.60)),
        ((7.15, 4.60), (7.95, 4.60)),
        ((9.65, 4.60), (10.45, 4.60)),
        ((12.15, 4.60), (13.00, 4.60)),
    ]:
        add_arrow(ax, start, end, "#555555")

    # Learning layer.
    y_learn = 2.43
    add_box(ax, (1.00, y_learn), 1.95, 0.65, "Teacher Supervision", "软标签 / 排序偏好", "#805A86")
    add_box(ax, (3.80, y_learn), 2.05, 0.65, "Alignment Teacher", "局部语义对齐", "#805A86", "#FFF9FF")
    add_box(ax, (6.70, y_learn), 2.05, 0.65, "多视角视频特征", "多帧 / 多时间窗", "#805A86", "#FFF9FF")
    add_box(ax, (9.60, y_learn), 2.05, 0.65, "学生检索模型", "adapter 表征增强", "#805A86")
    add_box(ax, (12.50, y_learn), 2.05, 0.65, "反馈记忆", "失败样本 / memory", "#805A86")

    for start, end in [
        ((2.95, 2.76), (3.80, 2.76)),
        ((5.85, 2.76), (6.70, 2.76)),
        ((8.75, 2.76), (9.60, 2.76)),
        ((11.65, 2.76), (12.50, 2.76)),
    ]:
        add_arrow(ax, start, end, "#805A86")

    # Frontend layer.
    y_ui = 1.02
    add_box(ax, (1.45, y_ui), 1.95, 0.48, "前端检索", "查询 / 参数", "#6B7280")
    add_box(ax, (4.45, y_ui), 1.95, 0.48, "结果展示", "Top-5 播放", "#6B7280")
    add_box(ax, (7.45, y_ui), 1.95, 0.48, "历史记录", "最近10次", "#6B7280")
    add_box(ax, (10.45, y_ui), 1.95, 0.48, "学习日志", "晋升 / 拒绝", "#6B7280")
    add_box(ax, (13.45, y_ui), 1.55, 0.48, "论文图表", "实验可视化", "#6B7280")

    for start, end in [
        ((3.40, 1.26), (4.45, 1.26)),
        ((6.40, 1.26), (7.45, 1.26)),
        ((9.40, 1.26), (10.45, 1.26)),
        ((12.40, 1.26), (13.45, 1.26)),
    ]:
        add_arrow(ax, start, end, "#6B7280")

    # Cross-layer dependencies.
    add_arrow(ax, (11.30, 6.10), (6.25, 4.95), "#486F95", rad=0.08, lw=1.0)
    add_note(ax, 8.55, 5.56, "索引供在线召回调用", "#486F95")
    add_arrow(ax, (10.62, 3.08), (6.25, 4.28), "#805A86", rad=-0.10, lw=1.0)
    add_note(ax, 8.00, 3.70, "增强后的检索模型参与在线召回", "#805A86")
    add_arrow(ax, (13.52, 4.27), (13.52, 3.08), "#805A86", lw=1.0)
    add_note(ax, 14.35, 3.65, "反馈写入 memory", "#805A86")
    add_arrow(ax, (11.42, 2.43), (11.42, 1.50), "#6B7280", lw=1.0)
    add_note(ax, 12.22, 1.95, "学习过程可视化", "#6B7280")

    ax.text(
        8.1,
        0.34,
        "说明：离线阶段负责视频特征与索引构建，在线阶段负责文本检索与结果展示；"
        "学习层通过教师监督与反馈记忆增强检索模型，并由前端页面展示检索与学习过程。",
        ha="center",
        va="center",
        fontsize=10.0,
        color="#333333",
    )

    fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    print(f"[OK] wrote {OUT_PNG}")
    print(f"[OK] wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
