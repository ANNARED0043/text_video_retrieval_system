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


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure candidate recall at top-k videos for a retrieval baseline.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--topk", type=int, default=30)
    parser.add_argument("--max_queries", type=int, default=0)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

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
    cutoffs = [1, 5, 10, args.topk]
    hits = {cutoff: 0 for cutoff in cutoffs}

    for row in tqdm(queries, desc=f"Candidate recall@{args.topk}", dynamic_ncols=True):
        seg_results = searcher.search(row["query"], topk=args.topk)
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
    payload = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "dataset": "MSR-VTT",
        "protocol": args.manifest.replace(".jsonl", ""),
        "model_name": args.model_name,
        "pretrained": args.pretrained,
        "candidate_topk": args.topk,
        "queries": n_queries,
        "candidate_recall": {
            f"R@{cutoff}": round(hits[cutoff] / max(1, n_queries) * 100.0, 2)
            for cutoff in cutoffs
        },
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[OK] wrote candidate recall: {out_path}")


if __name__ == "__main__":
    main()
