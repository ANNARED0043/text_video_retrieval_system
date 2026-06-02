from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.evaluation.evaluator_msrvtt import load_manifest_segment_to_video, load_queries_jsonl
from src.retrieval.searcher import FaissSearcher


def _parse_cutoffs(text: str) -> list[int]:
    cutoffs = sorted({int(item.strip()) for item in text.split(",") if item.strip()})
    if not cutoffs:
        raise ValueError("At least one cutoff is required.")
    return cutoffs


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate candidate recall sweep and save a line chart.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--cutoffs", type=str, default="1,5,10,20,30,40,50")
    parser.add_argument("--max_queries", type=int, default=0)
    parser.add_argument("--out_json", type=str, required=True)
    parser.add_argument("--out_png", type=str, required=True)
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for plotting the candidate recall curve.") from exc

    cutoffs = _parse_cutoffs(args.cutoffs)
    max_topk = max(cutoffs)

    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / args.manifest
    queries_path = cfg.paths.data_dir / "annotations" / "msrvtt" / args.queries
    index_dir = (
        cfg.paths.data_dir
        / "indexes"
        / args.manifest.replace(".jsonl", "")
        / args.pooling
        / f"{args.model_name}_{args.pretrained}".replace("/", "_")
        / "flat_ip"
    )

    seg2vid = load_manifest_segment_to_video(str(manifest_path))
    queries = load_queries_jsonl(str(queries_path))
    if args.max_queries > 0:
        queries = queries[: args.max_queries]
    searcher = FaissSearcher(str(index_dir), model_name=args.model_name, pretrained=args.pretrained)

    hits = {cutoff: 0 for cutoff in cutoffs}
    for row in tqdm(queries, desc=f"Candidate recall sweep up to {max_topk}", dynamic_ncols=True):
        seg_results = searcher.search(row["query"], topk=max_topk)
        ranked_videos: list[str] = []
        seen: set[str] = set()
        for seg_id, _score in seg_results:
            video_id = seg2vid.get(seg_id)
            if video_id is None or video_id in seen:
                continue
            seen.add(video_id)
            ranked_videos.append(video_id)
        for cutoff in cutoffs:
            if row["gt_video_id"] in ranked_videos[:cutoff]:
                hits[cutoff] += 1

    n_queries = len(queries)
    recall_points = [{"k": cutoff, "recall": round(hits[cutoff] / max(1, n_queries) * 100.0, 2)} for cutoff in cutoffs]
    deltas = []
    for prev, curr in zip(recall_points, recall_points[1:]):
        deltas.append({"from_k": prev["k"], "to_k": curr["k"], "gain": round(curr["recall"] - prev["recall"], 2)})

    payload = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "dataset": "MSR-VTT",
        "protocol": args.manifest.replace(".jsonl", ""),
        "model_name": args.model_name,
        "pretrained": args.pretrained,
        "queries": n_queries,
        "cutoffs": cutoffs,
        "recall_points": recall_points,
        "incremental_gains": deltas,
    }

    out_json = Path(args.out_json)
    if not out_json.is_absolute():
        out_json = PROJECT_ROOT / out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    ks = [point["k"] for point in recall_points]
    recalls = [point["recall"] for point in recall_points]
    plt.figure(figsize=(8, 5))
    plt.plot(ks, recalls, marker="o", linewidth=2.0, color="#1f77b4")
    for point in recall_points:
        plt.annotate(f"{point['recall']:.2f}", (point["k"], point["recall"]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    plt.title("Baseline Candidate Recall Curve on MSRVTT 1kA")
    plt.xlabel("Candidate Top-k")
    plt.ylabel("Recall (%)")
    plt.grid(alpha=0.25)
    plt.xticks(ks)
    plt.ylim(bottom=0.0, top=min(100.0, max(recalls) + 5.0))
    plt.tight_layout()

    out_png = Path(args.out_png)
    if not out_png.is_absolute():
        out_png = PROJECT_ROOT / out_png
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=160)
    plt.close()

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[OK] wrote candidate recall sweep json: {out_json}")
    print(f"[OK] wrote candidate recall sweep plot: {out_png}")


if __name__ == "__main__":
    main()
