from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.features.clip_encoder import encode_images, load_clip
from src.features.temporal_pooling import mean_pool
from src.utils.video_utils import sample_frames


DEFAULT_VIEW_NAMES = ["early", "middle", "late"]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _target_video_ids(
    *,
    queries_paths: list[Path],
    teacher_supervision_path: Path | None,
    max_query_rows: int,
    include_teacher_targets: bool,
) -> set[str]:
    video_ids: set[str] = set()
    qids: set[str] = set()
    for queries_path in queries_paths:
        rows = _read_jsonl(queries_path)
        if max_query_rows > 0:
            rows = rows[:max_query_rows]
        for row in rows:
            qids.add(str(row.get("qid", "")))
            gt_video_id = str(row.get("gt_video_id", ""))
            if gt_video_id:
                video_ids.add(gt_video_id)
    if teacher_supervision_path is not None and teacher_supervision_path.exists():
        for row in _read_jsonl(teacher_supervision_path):
            qid = str(row.get("qid", ""))
            if qids and qid not in qids:
                continue
            gt_video_id = str(row.get("gt_video_id", ""))
            if gt_video_id:
                video_ids.add(gt_video_id)
            if not include_teacher_targets:
                continue
            for key in ("similarity_targets", "listwise_targets"):
                for target in row.get(key, []):
                    video_id = str(target.get("video_id", ""))
                    if video_id:
                        video_ids.add(video_id)
            for video_id in row.get("hard_negatives", []):
                if video_id:
                    video_ids.add(str(video_id))
    return video_ids


def _view_names(view_segments: int) -> list[str]:
    if view_segments == 3:
        return DEFAULT_VIEW_NAMES
    return [f"view_{idx + 1:02d}" for idx in range(view_segments)]


def _view_windows(start_sec: float, end_sec: float, view_segments: int) -> list[tuple[float, float]]:
    duration = max(end_sec - start_sec, 0.03)
    step = duration / max(view_segments, 1)
    return [
        (start_sec + idx * step, start_sec + (idx + 1) * step)
        for idx in range(max(view_segments, 1))
    ]


def _fallback_frame(row: dict[str, Any]) -> list[np.ndarray]:
    start_sec = float(row.get("start_sec", 0.0))
    end_sec = float(row.get("end_sec", row.get("duration_sec", start_sec + 1.0)))
    mid = (start_sec + end_sec) / 2.0
    return sample_frames(row["video_path"], mid, min(mid + 0.05, end_sec), fps=1)


def build_multiview_features(
    *,
    manifest_name: str,
    out: str,
    frames_per_view: int,
    max_videos: int,
    model_name: str,
    pretrained: str,
    batch_size: int,
    queries: list[str],
    teacher_supervision: str,
    max_query_rows: int,
    include_teacher_targets: bool,
    view_segments: int,
) -> None:
    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / manifest_name
    rows = _read_jsonl(manifest_path)

    queries_paths = [cfg.paths.data_dir / "annotations" / "msrvtt" / item for item in queries]
    teacher_path = Path(teacher_supervision) if teacher_supervision.strip() else None
    if teacher_path is not None and not teacher_path.is_absolute():
        teacher_path = PROJECT_ROOT / teacher_path
    target_ids = _target_video_ids(
        queries_paths=queries_paths,
        teacher_supervision_path=teacher_path,
        max_query_rows=max_query_rows,
        include_teacher_targets=include_teacher_targets,
    ) if queries_paths or teacher_path else set()
    if target_ids:
        rows = [row for row in rows if str(row.get("video_id", "")) in target_ids]
    if max_videos > 0:
        rows = rows[:max_videos]

    clip = load_clip(model_name=model_name, pretrained=pretrained)
    view_names = _view_names(view_segments)
    video_ids: list[str] = []
    feature_rows: list[np.ndarray] = []

    for row in tqdm(rows, desc="Build multiview video features", dynamic_ncols=True):
        start_sec = float(row.get("start_sec", 0.0))
        end_sec = float(row.get("end_sec", row.get("duration_sec", start_sec + 1.0)))
        view_vectors: list[np.ndarray] = []
        fallback = None
        for view_start, view_end in _view_windows(start_sec, end_sec, view_segments):
            frames = sample_frames(row["video_path"], view_start, view_end, fps=max(frames_per_view, 1))
            if len(frames) > frames_per_view:
                frames = frames[:frames_per_view]
            if not frames:
                if fallback is None:
                    fallback = _fallback_frame(row)
                frames = fallback
            if not frames:
                break
            frame_feats = encode_images(clip, frames, batch_size=batch_size)
            view_vectors.append(mean_pool(frame_feats))
        if len(view_vectors) != len(view_names):
            continue
        video_ids.append(str(row["video_id"]))
        feature_rows.append(np.stack(view_vectors, axis=0).astype(np.float32))

    out_path = PROJECT_ROOT / out if not Path(out).is_absolute() else Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    features = (
        np.stack(feature_rows, axis=0).astype(np.float32)
        if feature_rows else np.zeros((0, len(view_names), 0), dtype=np.float32)
    )
    np.savez_compressed(
        out_path,
        video_ids=np.asarray(video_ids),
        view_names=np.asarray(view_names),
        features=features,
    )
    print(json.dumps({
        "out": str(out_path),
        "videos": len(video_ids),
        "views": view_names,
        "feature_shape": list(features.shape),
        "target_filter": {
            "requested_video_ids": len(target_ids),
            "matched_manifest_rows": len(rows),
            "include_teacher_targets": include_teacher_targets,
            "max_query_rows": max_query_rows,
        },
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build temporal multi-view CLIP video features.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--frames_per_view", type=int, default=2)
    parser.add_argument("--max_videos", type=int, default=0)
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--queries", action="append", default=[])
    parser.add_argument("--teacher_supervision", type=str, default="")
    parser.add_argument("--max_query_rows", type=int, default=0)
    parser.add_argument("--include_teacher_targets", action="store_true")
    parser.add_argument("--view_segments", type=int, default=3)
    args = parser.parse_args()
    build_multiview_features(
        manifest_name=args.manifest,
        out=args.out,
        frames_per_view=args.frames_per_view,
        max_videos=args.max_videos,
        model_name=args.model_name,
        pretrained=args.pretrained,
        batch_size=args.batch_size,
        queries=args.queries,
        teacher_supervision=args.teacher_supervision,
        max_query_rows=args.max_query_rows,
        include_teacher_targets=args.include_teacher_targets,
        view_segments=args.view_segments,
    )


if __name__ == "__main__":
    main()
