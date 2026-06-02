from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.data.msrvtt_loader import load_msrvtt_videodatainfo, load_video_list, make_test_queries
from src.utils.research_log import append_research_log


def _filter_queries_by_video(query_path: Path, keep_videos: set[str], out_path: Path) -> int:
    rows: list[dict] = []
    with query_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("gt_video_id") in keep_videos:
                rows.append(row)
    for idx, row in enumerate(rows):
        row["qid"] = idx
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _filter_manifest_by_video(manifest_path: Path, keep_videos: set[str], out_path: Path) -> int:
    rows: list[dict] = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("video_id") in keep_videos:
                rows.append(row)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _valid_feature_videos(
    manifests_dir: Path,
    data_dir: Path,
    manifest_name: str,
    pooling: str,
    model_name: str,
    pretrained: str,
) -> tuple[set[str], list[str]]:
    manifest_path = manifests_dir / manifest_name
    feature_dir = data_dir / "features" / manifest_name.replace(".jsonl", "") / pooling / f"{model_name}_{pretrained}".replace("/", "_")
    valid_videos: set[str] = set()
    invalid_videos: list[str] = []
    seen: set[str] = set()

    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            video_id = row.get("video_id")
            segment_id = row.get("segment_id")
            if not video_id or not segment_id or video_id in seen:
                continue
            seen.add(video_id)
            feature_path = feature_dir / f"{segment_id}.npy"
            try:
                if not feature_path.exists() or feature_path.stat().st_size == 0:
                    raise FileNotFoundError(str(feature_path))
                np.load(feature_path, mmap_mode="r")
                valid_videos.add(video_id)
            except Exception:
                invalid_videos.append(video_id)
    return valid_videos, invalid_videos


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a leakage-safe train/dev split from MSRVTT train_9k.")
    parser.add_argument("--seed", type=int, default=20260409)
    parser.add_argument("--dev_videos", type=int, default=1000)
    parser.add_argument(
        "--train_queries_in",
        type=str,
        default="msrvtt_train_9k_queries.jsonl",
    )
    parser.add_argument(
        "--safe_train_queries_out",
        type=str,
        default="msrvtt_train_9k_safe_train_queries.jsonl",
    )
    parser.add_argument(
        "--safe_dev_queries_out",
        type=str,
        default="msrvtt_train_9k_safe_dev_queries.jsonl",
    )
    parser.add_argument(
        "--safe_dev_list_out",
        type=str,
        default="safe_dev_video_list.txt",
    )
    parser.add_argument(
        "--full_manifest_in",
        type=str,
        default="msrvtt_fixed.jsonl",
    )
    parser.add_argument(
        "--safe_dev_manifest_out",
        type=str,
        default="msrvtt_fixed_safe_dev.jsonl",
    )
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    args = parser.parse_args()

    cfg = load_config()
    ann_dir = cfg.paths.data_dir / "annotations" / "msrvtt"
    manifests_dir = cfg.paths.manifests_dir
    train_list_path = ann_dir / "train_list_jsfusion_clean.txt"
    ann_json = ann_dir / "MSRVTT_data.json"
    train_queries_in = ann_dir / args.train_queries_in
    safe_train_queries_out = ann_dir / args.safe_train_queries_out
    safe_dev_queries_out = ann_dir / args.safe_dev_queries_out
    safe_dev_list_out = ann_dir / args.safe_dev_list_out
    full_manifest_in = manifests_dir / args.full_manifest_in
    safe_dev_manifest_out = manifests_dir / args.safe_dev_manifest_out

    if not train_list_path.exists():
        raise FileNotFoundError(f"Missing train split list: {train_list_path}")
    if not ann_json.exists():
        raise FileNotFoundError(f"Missing annotations: {ann_json}")
    if not train_queries_in.exists():
        raise FileNotFoundError(f"Missing train queries: {train_queries_in}")
    if not full_manifest_in.exists():
        raise FileNotFoundError(f"Missing full manifest: {full_manifest_in}")

    train_videos = load_video_list(str(train_list_path))
    valid_videos, invalid_videos = _valid_feature_videos(
        manifests_dir=manifests_dir,
        data_dir=cfg.paths.data_dir,
        manifest_name=args.full_manifest_in,
        pooling=args.pooling,
        model_name=args.model_name,
        pretrained=args.pretrained,
    )
    train_videos = [video_id for video_id in train_videos if video_id in valid_videos]
    if args.dev_videos <= 0 or args.dev_videos >= len(train_videos):
        raise ValueError(f"dev_videos must be in [1, {len(train_videos) - 1}]")

    rng = random.Random(args.seed)
    dev_videos = sorted(rng.sample(train_videos, args.dev_videos))
    dev_video_set = set(dev_videos)
    safe_train_videos = [video_id for video_id in train_videos if video_id not in dev_video_set]

    safe_dev_list_out.write_text("\n".join(dev_videos) + "\n", encoding="utf-8")
    train_query_count = _filter_queries_by_video(train_queries_in, set(safe_train_videos), safe_train_queries_out)
    safe_dev_manifest_rows = _filter_manifest_by_video(full_manifest_in, dev_video_set, safe_dev_manifest_out)

    video_to_caps = load_msrvtt_videodatainfo(str(ann_json))
    make_test_queries(video_to_caps, dev_videos, str(safe_dev_queries_out), max_caps_per_video=5)

    summary = (
        f"Created leakage-safe train/dev split from train_9k with seed={args.seed}, "
        f"dev_videos={len(dev_videos)}, train_videos={len(safe_train_videos)}."
    )
    append_research_log(
        step="prepare_msrvtt_safe_split",
        summary=summary,
        decisions=[
            "Use only train_9k videos to derive the quick-gate dev split.",
            "Keep the official 1kA test split out of hyperparameter tuning and model selection.",
            "Make the split video-disjoint so the same video never appears in both train and dev queries.",
        ],
        citations=[
            "fine_grained_accv2024",
            "discovla_cvpr2025",
        ],
        artifacts=[
            str(safe_train_queries_out),
            str(safe_dev_queries_out),
            str(safe_dev_list_out),
            str(safe_dev_manifest_out),
        ],
        extra={
            "seed": args.seed,
            "dev_videos": len(dev_videos),
            "train_videos": len(safe_train_videos),
            "safe_train_queries": train_query_count,
            "safe_dev_manifest_rows": safe_dev_manifest_rows,
            "invalid_videos_excluded": len(invalid_videos),
        },
    )

    print(f"[OK] safe_train_videos={len(safe_train_videos)}")
    print(f"[OK] safe_dev_videos={len(dev_videos)}")
    print(f"[OK] invalid_videos_excluded={len(invalid_videos)}")
    print(f"[OK] wrote safe train queries: {safe_train_queries_out}")
    print(f"[OK] wrote safe dev queries: {safe_dev_queries_out}")
    print(f"[OK] wrote safe dev list: {safe_dev_list_out}")
    print(f"[OK] wrote safe dev manifest: {safe_dev_manifest_out}")


if __name__ == "__main__":
    main()
