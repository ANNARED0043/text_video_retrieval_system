"""Create a small 1kA subset for quick mean/max pooling ablation."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "data" / "manifests"
QUERY_DIR = ROOT / "data" / "annotations" / "msrvtt"


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _video_id(row: dict) -> str:
    if "video_id" in row:
        return str(row["video_id"])
    segment_id = str(row.get("segment_id", ""))
    if "_" in segment_id:
        return segment_id.split("_")[0]
    return segment_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--videos", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260428)
    parser.add_argument("--out_manifest", default="msrvtt_fixed_1kA_pooling_smoke200.jsonl")
    parser.add_argument("--out_queries", default="msrvtt_1kA_pooling_smoke200_queries.jsonl")
    args = parser.parse_args()

    manifest_rows = _read_jsonl(MANIFEST_DIR / args.manifest)
    query_rows = _read_jsonl(QUERY_DIR / args.queries)
    query_video_ids = {str(row["gt_video_id"]) for row in query_rows}

    video_to_rows: dict[str, list[dict]] = {}
    for row in manifest_rows:
        video_to_rows.setdefault(_video_id(row), []).append(row)

    candidate_video_ids = sorted(set(video_to_rows) & query_video_ids)
    rng = random.Random(args.seed)
    selected_ids = set(rng.sample(candidate_video_ids, min(args.videos, len(candidate_video_ids))))

    subset_manifest = [
        row for video_id in sorted(selected_ids) for row in video_to_rows[video_id]
    ]
    subset_queries = [
        row for row in query_rows if str(row["gt_video_id"]) in selected_ids
    ]

    _write_jsonl(MANIFEST_DIR / args.out_manifest, subset_manifest)
    _write_jsonl(QUERY_DIR / args.out_queries, subset_queries)

    print(
        json.dumps(
            {
                "out_manifest": str(MANIFEST_DIR / args.out_manifest),
                "out_queries": str(QUERY_DIR / args.out_queries),
                "videos": len(selected_ids),
                "manifest_rows": len(subset_manifest),
                "queries": len(subset_queries),
                "seed": args.seed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
