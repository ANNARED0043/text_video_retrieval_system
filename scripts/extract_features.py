"""Extract CLIP features for each manifest segment."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tqdm import tqdm

from src.config import load_config
from src.features.clip_encoder import encode_images, load_clip
from src.features.feature_store import exists, save_feature
from src.features.temporal_pooling import pool
from src.utils.video_utils import sample_frames


def iter_manifest(jsonl_path: str):
    with open(jsonl_path, "r", encoding="utf-8") as fin:
        for line in fin:
            if line.strip():
                yield json.loads(line)


def main(
    manifest_name: str = "segments_fixed.jsonl",
    pooling_mode: str = "mean",
    sample_fps: int = 2,
    batch_size: int = 16,
    model_name: str = "ViT-B-32",
    pretrained: str = "openai",
):
    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / manifest_name
    if not manifest_path.exists():
        raise RuntimeError(f"Manifest not found: {manifest_path}. Run scripts/build_manifests.py first.")

    model_suffix = f"{model_name}_{pretrained}".replace("/", "_")
    out_dir = (
        cfg.paths.data_dir
        / "features"
        / manifest_name.replace(".jsonl", "")
        / pooling_mode
        / model_suffix
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    clip = load_clip(model_name=model_name, pretrained=pretrained)
    rows = list(iter_manifest(str(manifest_path)))

    for row in tqdm(rows, desc=f"Extracting ({manifest_name}, pool={pooling_mode}, model={model_name})"):
        seg_id = row["segment_id"]
        if exists(str(out_dir), seg_id):
            continue

        frames = sample_frames(
            row["video_path"],
            float(row["start_sec"]),
            float(row["end_sec"]),
            fps=sample_fps,
        )
        if len(frames) == 0:
            continue

        frame_feats = encode_images(clip, frames, batch_size=batch_size)
        seg_vec = pool(frame_feats, mode=pooling_mode)
        save_feature(str(out_dir), seg_id, seg_vec)

    print(f"[OK] features saved to: {out_dir}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, required=True, help="Manifest jsonl file name in data/manifests/")
    parser.add_argument("--pooling", type=str, default="mean", choices=["mean", "max"], help="Pooling mode")
    parser.add_argument("--fps", type=int, default=2, help="Sampling FPS within each segment")
    parser.add_argument("--batch", type=int, default=16, help="Batch size for CLIP encoding")
    parser.add_argument("--model_name", type=str, default="ViT-B-32", help="OpenCLIP model name")
    parser.add_argument("--pretrained", type=str, default="openai", help="OpenCLIP pretrained tag")
    args = parser.parse_args()

    main(
        manifest_name=args.manifest,
        pooling_mode=args.pooling,
        sample_fps=args.fps,
        batch_size=args.batch,
        model_name=args.model_name,
        pretrained=args.pretrained,
    )
