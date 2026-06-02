"""Build a FAISS index from extracted CLIP features."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.retrieval.index_builder import (
    build_faiss_flat_index,
    load_segment_ids_from_manifest,
    save_index,
)


def main(
    manifest_name: str,
    pooling_mode: str = "mean",
    model_name: str = "ViT-B-32",
    pretrained: str = "openai",
    features_from_manifest: str = "",
):
    cfg = load_config()

    manifest_path = cfg.paths.manifests_dir / manifest_name
    if not manifest_path.exists():
        raise RuntimeError(f"Manifest not found: {manifest_path}")

    model_suffix = f"{model_name}_{pretrained}".replace("/", "_")
    feature_manifest_name = features_from_manifest or manifest_name
    features_dir = (
        cfg.paths.data_dir
        / "features"
        / feature_manifest_name.replace(".jsonl", "")
        / pooling_mode
        / model_suffix
    )
    if not features_dir.exists():
        raise RuntimeError(f"Features not found: {features_dir}. Run scripts/extract_features.py first.")

    out_dir = (
        cfg.paths.data_dir
        / "indexes"
        / manifest_name.replace(".jsonl", "")
        / pooling_mode
        / model_suffix
        / "flat_ip"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    segment_ids = load_segment_ids_from_manifest(str(manifest_path))
    index, _ = build_faiss_flat_index(str(features_dir), segment_ids)
    save_index(index, segment_ids, str(out_dir))
    print(f"[OK] index saved to: {out_dir}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, required=True, help="Manifest jsonl file name in data/manifests/")
    parser.add_argument("--pooling", type=str, default="mean", choices=["mean", "max"], help="Pooling mode")
    parser.add_argument("--model_name", type=str, default="ViT-B-32", help="OpenCLIP model name")
    parser.add_argument("--pretrained", type=str, default="openai", help="OpenCLIP pretrained tag")
    parser.add_argument(
        "--features_from_manifest",
        type=str,
        default="",
        help="Optional manifest stem whose feature directory should be reused when building a subset index.",
    )
    args = parser.parse_args()

    main(
        manifest_name=args.manifest,
        pooling_mode=args.pooling,
        model_name=args.model_name,
        pretrained=args.pretrained,
        features_from_manifest=args.features_from_manifest,
    )
