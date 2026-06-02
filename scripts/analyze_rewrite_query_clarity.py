"""Analyze when query rewriting helps on MSR-VTT.

This script compares per-query baseline ranks with an existing rewrite log.
It is designed for thesis diagnostics: whether rewrite gains are limited
because most MSR-VTT queries are already clear.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.evaluation.evaluator_msrvtt import (  # noqa: E402
    load_manifest_segment_to_video,
    load_queries_jsonl,
)
from src.retrieval.searcher import FaissSearcher  # noqa: E402


GENERIC_WORDS = {
    "person",
    "people",
    "someone",
    "somebody",
    "something",
    "stuff",
    "thing",
    "things",
    "some",
    "various",
}

ACTION_LIGHT_WORDS = {
    "doing",
    "making",
    "preparing",
    "creating",
    "working",
    "playing",
    "talking",
    "showing",
    "using",
}

SCENE_WORDS = {
    "inside",
    "outside",
    "outdoors",
    "indoor",
    "outdoor",
    "room",
    "kitchen",
    "field",
    "studio",
    "stage",
    "street",
}

ATTRIBUTE_WORDS = {
    "young",
    "old",
    "boy",
    "girl",
    "man",
    "woman",
    "child",
    "hair",
    "glasses",
    "shirt",
    "jacket",
    "red",
    "black",
    "white",
    "blonde",
}


def _model_suffix(model_name: str, pretrained: str) -> str:
    return f"{model_name}_{pretrained}".replace("/", "_")


def _segment_results_to_video_scores(
    seg_results: list[tuple[str, float]],
    seg2vid: dict[str, str],
) -> dict[str, float]:
    vid2score: dict[str, float] = {}
    for seg_id, score in seg_results:
        vid = seg2vid.get(seg_id)
        if vid is None:
            continue
        prev = vid2score.get(vid)
        score = float(score)
        if prev is None or score > prev:
            vid2score[vid] = score
    return vid2score


def _rank_query(
    searcher: FaissSearcher,
    query: str,
    gt_video_id: str,
    seg2vid: dict[str, str],
    topk: int,
) -> int:
    seg_results = searcher.search(query, topk=topk)
    vid2score = _segment_results_to_video_scores(seg_results, seg2vid)
    ranked = sorted(vid2score.items(), key=lambda item: item[1], reverse=True)
    for idx, (video_id, _) in enumerate(ranked, start=1):
        if video_id == gt_video_id:
            return idx
    return len(ranked) + 1


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _has_generic_language(query: str) -> bool:
    tokens = {token.strip(".,;:!?()[]{}\"'").lower() for token in query.split()}
    return bool(tokens & GENERIC_WORDS)


def _query_issue_tags(query: str) -> list[str]:
    tokens = [token.strip(".,;:!?()[]{}\"'").lower() for token in query.split()]
    token_set = set(tokens)
    tags: list[str] = []
    if token_set & GENERIC_WORDS:
        tags.append("generic_object")
    if token_set & ACTION_LIGHT_WORDS:
        tags.append("weak_action")
    if not (token_set & SCENE_WORDS):
        tags.append("scene_missing")
    if not (token_set & ATTRIBUTE_WORDS):
        tags.append("attribute_missing")
    if len(tokens) <= 6:
        tags.append("short_query")
    return tags or ["relatively_clear"]


def _transition_label(base_rank: int, rewrite_rank: int) -> str:
    if base_rank > 1 and rewrite_rank == 1:
        return "fixed_to_top1"
    if base_rank == 1 and rewrite_rank > 1:
        return "hurt_top1"
    if rewrite_rank < base_rank:
        return "improved_rank"
    if rewrite_rank > base_rank:
        return "worse_rank"
    return "unchanged"


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "font.size": 10.5,
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Microsoft YaHei",
                "SimHei",
                "Noto Sans CJK SC",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
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


def _reason_label(reason: str) -> str:
    labels = {
        "generic_object": "对象表达\n较泛化",
        "weak_action": "动作表达\n较弱",
        "scene_missing": "场景约束\n缺失",
        "attribute_missing": "属性约束\n缺失",
        "short_query": "查询文本\n较短",
        "relatively_clear": "语义相对\n清晰",
        "small_margin": "候选分差\n较小",
        "age_sensitive": "年龄/人物\n属性敏感",
        "count_sensitive": "数量关系\n敏感",
        "scene_constraint": "场景约束\n敏感",
        "low_top1": "首位置信度\n较低",
        "other": "其他",
        "none": "无",
    }
    return labels.get(reason, reason.replace("_", "\n"))


def _draw_figure(rows: list[dict[str, Any]], out_path: Path) -> None:
    _setup_style()
    used_rows = [row for row in rows if row["used_rewrite"]]
    clear_rows = [row for row in rows if not row["used_rewrite"]]

    transition_counts = Counter(row["transition"] for row in used_rows)
    reason_counts: Counter[str] = Counter()
    for row in used_rows:
        reason_counts.update(row["reasons"] or ["other"])

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17.4, 5.6),
        gridspec_kw={"width_ratios": [1.0, 1.55, 1.15]},
    )

    clarity_labels = ["未触发改写\n（语义较清晰）", "触发改写\n（需补充语义）"]
    clarity_values = [len(clear_rows), len(used_rows)]
    colors = ["#4C78A8", "#C44E52"]
    axes[0].bar(clarity_labels, clarity_values, color=colors, width=0.55)
    axes[0].set_ylabel("查询数量")
    axes[0].set_title("（a）选择性改写触发比例", pad=18)
    ymax = max(clarity_values) * 1.28
    axes[0].set_ylim(0, ymax)
    for idx, val in enumerate(clarity_values):
        axes[0].text(idx, val + ymax * 0.035, f"{val}\n{val / len(rows) * 100:.1f}%",
                     ha="center", va="bottom", fontsize=9)

    order = [
        "fixed_to_top1",
        "improved_rank",
        "unchanged",
        "worse_rank",
        "hurt_top1",
    ]
    labels = [
        "修正至\nTop-1",
        "排名\n提升",
        "排名\n不变",
        "排名\n下降",
        "Top-1\n被破坏",
    ]
    vals = [transition_counts.get(key, 0) for key in order]
    axes[1].bar(labels, vals, color="#59A14F", width=0.62)
    axes[1].set_title("（b）改写后的排名变化", pad=18)
    axes[1].tick_params(axis="x", labelrotation=0)
    axes[1].set_ylim(0, max(vals + [1]) * 1.24)
    for idx, val in enumerate(vals):
        axes[1].text(idx, val + 1, str(val), ha="center", va="bottom", fontsize=9)

    if reason_counts:
        reason_items = reason_counts.most_common(5)
        reason_labels = [_reason_label(item[0]) for item in reason_items]
        reason_vals = [item[1] for item in reason_items]
    else:
        reason_labels, reason_vals = [_reason_label("none")], [0]
    axes[2].barh(reason_labels[::-1], reason_vals[::-1], color="#F58518")
    axes[2].set_xlabel("出现次数")
    axes[2].set_title("（c）触发改写的语义原因", pad=18)
    for idx, val in enumerate(reason_vals[::-1]):
        axes[2].text(val + 0.5, idx, str(val), va="center", fontsize=9)

    fig.suptitle("MSR-VTT 1kA q200 选择性查询改写适用边界诊断", y=1.02, fontsize=13)
    fig.subplots_adjust(wspace=0.36, top=0.78, bottom=0.24)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", default="mean", choices=["mean", "max"])
    parser.add_argument("--topk", type=int, default=200)
    parser.add_argument("--model_name", default="ViT-H-14")
    parser.add_argument("--pretrained", default="laion2b_s32b_b79k")
    parser.add_argument(
        "--rewrite_log",
        default="outputs/tables/final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75.jsonl",
    )
    parser.add_argument(
        "--out_json",
        default="outputs/tables/analysis/rewrite_query_clarity_diagnosis_q200.json",
    )
    parser.add_argument(
        "--out_fig",
        default="outputs/figures/paper_fig5_rewrite_query_clarity_diagnosis.png",
    )
    args = parser.parse_args()

    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / args.manifest
    queries_path = cfg.paths.data_dir / "annotations" / "msrvtt" / args.queries
    index_dir = (
        cfg.paths.data_dir
        / "indexes"
        / args.manifest.replace(".jsonl", "")
        / args.pooling
        / _model_suffix(args.model_name, args.pretrained)
        / "flat_ip"
    )
    rewrite_rows = _load_jsonl(PROJECT_ROOT / args.rewrite_log)
    query_rows = load_queries_jsonl(str(queries_path))[: len(rewrite_rows)]
    seg2vid = load_manifest_segment_to_video(str(manifest_path))
    searcher = FaissSearcher(
        str(index_dir),
        model_name=args.model_name,
        pretrained=args.pretrained,
    )

    diagnosis_rows: list[dict[str, Any]] = []
    for rewrite_row, query_row in tqdm(
        list(zip(rewrite_rows, query_rows)),
        desc="Compare baseline and rewrite",
        dynamic_ncols=True,
    ):
        query = query_row["query"]
        gt_video_id = query_row["gt_video_id"]
        base_rank = _rank_query(searcher, query, gt_video_id, seg2vid, args.topk)
        rewrite_rank = int(rewrite_row["rank"])
        rewrite_info = rewrite_row.get("rewrite", {})
        ambiguity = rewrite_info.get("ambiguity", {})
        used_rewrite = bool(rewrite_info.get("used_rewrite", False))
        reasons = ambiguity.get("reasons", [])
        diagnosis_rows.append(
            {
                "qid": rewrite_row["qid"],
                "query": query,
                "rewritten_query": rewrite_info.get("rewritten_query", query),
                "gt_video_id": gt_video_id,
                "baseline_rank": base_rank,
                "rewrite_rank": rewrite_rank,
                "rank_delta": base_rank - rewrite_rank,
                "transition": _transition_label(base_rank, rewrite_rank),
                "used_rewrite": used_rewrite,
                "ambiguity_score": ambiguity.get("score", 0.0),
                "reasons": reasons,
                "token_count": ambiguity.get("token_count", len(query.split())),
                "has_generic_language": _has_generic_language(query),
                "issue_tags": _query_issue_tags(query),
            }
        )

    total = len(diagnosis_rows)
    used = [row for row in diagnosis_rows if row["used_rewrite"]]
    clear = [row for row in diagnosis_rows if not row["used_rewrite"]]
    fixed = [row for row in used if row["transition"] == "fixed_to_top1"]
    hurt = [row for row in used if row["transition"] == "hurt_top1"]
    improved = [row for row in used if row["rewrite_rank"] < row["baseline_rank"]]
    worse = [row for row in used if row["rewrite_rank"] > row["baseline_rank"]]

    useful_rewrite_rows = [
        row for row in used if row["transition"] in {"fixed_to_top1", "improved_rank"}
    ]
    useful_issue_counts: Counter[str] = Counter()
    for row in useful_rewrite_rows:
        useful_issue_counts.update(row["issue_tags"])

    payload = {
        "schema_version": "rewrite_query_clarity_diagnosis_v1",
        "total_queries": total,
        "rewrite_triggered": len(used),
        "rewrite_rate": round(len(used) / total, 4) if total else 0.0,
        "clear_or_not_rewritten": len(clear),
        "clear_or_not_rewritten_rate": round(len(clear) / total, 4) if total else 0.0,
        "rank_transition_counts": dict(Counter(row["transition"] for row in used)),
        "trigger_reason_counts": dict(
            Counter(reason for row in used for reason in (row["reasons"] or ["other"]))
        ),
        "generic_language_rate": round(
            sum(row["has_generic_language"] for row in diagnosis_rows) / total, 4
        )
        if total
        else 0.0,
        "generic_language_rate_rewritten": round(
            sum(row["has_generic_language"] for row in used) / len(used), 4
        )
        if used
        else 0.0,
        "baseline_top1": sum(row["baseline_rank"] == 1 for row in diagnosis_rows),
        "rewrite_top1": sum(row["rewrite_rank"] == 1 for row in diagnosis_rows),
        "rewrite_improved_count": len(improved),
        "rewrite_worse_count": len(worse),
        "useful_rewrite_count": len(useful_rewrite_rows),
        "useful_rewrite_issue_counts": dict(useful_issue_counts),
        "useful_rewrite_examples": useful_rewrite_rows,
        "fixed_to_top1_examples": fixed[:8],
        "hurt_top1_examples": hurt[:8],
        "improved_examples": improved[:8],
        "rows": diagnosis_rows,
    }

    out_json = PROJECT_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _draw_figure(diagnosis_rows, PROJECT_ROOT / args.out_fig)

    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, ensure_ascii=False, indent=2))
    print(f"[OK] wrote diagnosis: {out_json}")
    print(f"[OK] wrote figure: {PROJECT_ROOT / args.out_fig}")


if __name__ == "__main__":
    main()
