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
from src.features.clip_encoder import encode_images, encode_text, load_clip
from src.utils.video_utils import sample_frames


AGE_PROMPTS = {
    "baby": "a video frame showing a baby",
    "child": "a video frame showing a child",
    "teenager": "a video frame showing a teenager",
    "adult": "a video frame showing an adult person",
    "elderly": "a video frame showing an elderly person",
}

PERSON_PROMPTS = {
    "man": "a video frame showing a man",
    "woman": "a video frame showing a woman",
    "boy": "a video frame showing a boy",
    "girl": "a video frame showing a girl",
    "group": "a video frame showing a group of people",
    "couple": "a video frame showing a couple",
    "person_uncertain": "a video frame showing a person",
}

ACTION_PROMPTS = {
    "running": "a video frame of a person running",
    "walking": "a video frame of a person walking",
    "dancing": "a video frame of a person dancing",
    "singing": "a video frame of a person singing",
    "talking": "a video frame of a person talking",
    "cooking": "a video frame of a person cooking",
    "playing": "a video frame of a person playing",
    "driving": "a video frame of a person driving",
    "riding": "a video frame of a person riding",
    "swimming": "a video frame of a person swimming",
    "jumping": "a video frame of a person jumping",
    "eating": "a video frame of a person eating",
    "drinking": "a video frame of a person drinking",
    "holding": "a video frame of a person holding an object",
    "throwing": "a video frame of a person throwing",
    "cutting": "a video frame of a person cutting",
    "stirring": "a video frame of a person stirring",
    "mixing": "a video frame of a person mixing ingredients",
    "pouring": "a video frame of a person pouring liquid",
    "shooting": "a video frame of a person shooting a ball",
    "kicking": "a video frame of a person kicking",
    "reading": "a video frame of a person reading",
    "writing": "a video frame of a person writing",
    "speaking": "a video frame of a person speaking",
    "interviewing": "a video frame of a person interviewing",
    "exercising": "a video frame of a person exercising",
    "climbing": "a video frame of a person climbing",
    "falling": "a video frame of a person falling",
    "sitting": "a video frame of a person sitting",
    "standing": "a video frame of a person standing",
    "washing": "a video frame of a person washing",
    "cleaning": "a video frame of a person cleaning",
    "performing": "a video frame of a person performing",
    "demonstrating": "a video frame of a person demonstrating something",
}

SCENE_PROMPTS = {
    "indoor": "an indoor video frame",
    "outdoor": "an outdoor video frame",
    "kitchen": "a video frame in a kitchen",
    "street": "a video frame on a street",
    "stage": "a video frame on a stage",
    "sports_field": "a video frame on a sports field",
    "water": "a video frame near water",
    "court": "a video frame on a sports court",
    "news_studio": "a video frame in a news studio",
    "bedroom": "a video frame in a bedroom",
    "bathroom": "a video frame in a bathroom",
    "garage": "a video frame in a garage",
    "snow": "a video frame in snow",
    "mountain": "a video frame near a mountain",
    "garden": "a video frame in a garden",
    "market": "a video frame in a market",
    "classroom": "a video frame in a classroom",
    "concert": "a video frame at a concert",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def _normalize(vecs: np.ndarray) -> np.ndarray:
    return (vecs / (np.linalg.norm(vecs, axis=-1, keepdims=True) + 1e-12)).astype(np.float32)


def _softmax(scores: np.ndarray) -> np.ndarray:
    shifted = scores - float(np.max(scores))
    exp = np.exp(shifted)
    return exp / max(float(exp.sum()), 1e-8)


def _top_label(scores: np.ndarray, labels: list[str]) -> tuple[str, float]:
    probs = _softmax(scores)
    idx = int(np.argmax(probs))
    return labels[idx], float(probs[idx])


def _encode_prompt_bank(clip_bundle, prompts: dict[str, str]) -> tuple[list[str], np.ndarray]:
    labels = list(prompts.keys())
    feats = [encode_text(clip_bundle, prompts[label]) for label in labels]
    return labels, _normalize(np.stack(feats, axis=0))


def _frame_times(start_sec: float, end_sec: float, count: int) -> list[float]:
    if count <= 1:
        return [(start_sec + end_sec) / 2.0]
    margin = max((end_sec - start_sec) * 0.04, 0.01)
    return np.linspace(start_sec + margin, end_sec - margin, count).astype(float).tolist()


def _sample_sparse_frames(row: dict[str, Any], frames_per_video: int) -> list[np.ndarray]:
    start_sec = float(row.get("start_sec", 0.0))
    end_sec = float(row.get("end_sec", row.get("duration_sec", start_sec + 1.0)))
    frames: list[np.ndarray] = []
    # Reuse the project sampler with one-frame micro windows so we keep ordering.
    for timestamp in _frame_times(start_sec, end_sec, frames_per_video):
        sampled = sample_frames(row["video_path"], timestamp, min(timestamp + 0.01, end_sec), fps=1)
        if sampled:
            frames.append(sampled[0])
    return frames


def _group_scores(frame_feats: np.ndarray, prompt_feats: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    frame_scores = frame_feats @ prompt_feats.T
    video_scores = frame_scores.mean(axis=0)
    return frame_scores, video_scores


def build_alignment_teacher(
    *,
    manifest_name: str,
    out: str,
    frames_per_video: int,
    max_videos: int,
    model_name: str,
    pretrained: str,
    batch_size: int,
    queries: list[str],
    teacher_supervision: str,
    max_query_rows: int,
    include_teacher_targets: bool,
) -> None:
    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / manifest_name
    rows = _read_jsonl(manifest_path)
    queries_paths = [cfg.paths.data_dir / "annotations" / "msrvtt" / item for item in queries]
    teacher_supervision_path = Path(teacher_supervision) if teacher_supervision.strip() else None
    if teacher_supervision_path is not None and not teacher_supervision_path.is_absolute():
        teacher_supervision_path = PROJECT_ROOT / teacher_supervision_path
    target_video_ids = _target_video_ids(
        queries_paths=queries_paths,
        teacher_supervision_path=teacher_supervision_path,
        max_query_rows=max_query_rows,
        include_teacher_targets=include_teacher_targets,
    ) if queries_paths or teacher_supervision_path else set()
    if target_video_ids:
        rows = [row for row in rows if str(row.get("video_id", "")) in target_video_ids]
    if max_videos > 0:
        rows = rows[:max_videos]

    clip_bundle = load_clip(model_name=model_name, pretrained=pretrained)
    age_labels, age_prompts = _encode_prompt_bank(clip_bundle, AGE_PROMPTS)
    person_labels, person_prompts = _encode_prompt_bank(clip_bundle, PERSON_PROMPTS)
    action_labels, action_prompts = _encode_prompt_bank(clip_bundle, ACTION_PROMPTS)
    scene_labels, scene_prompts = _encode_prompt_bank(clip_bundle, SCENE_PROMPTS)

    out_path = PROJECT_ROOT / out if not Path(out).is_absolute() else Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        for row in tqdm(rows, desc="Build multiframe alignment teacher", dynamic_ncols=True):
            frames = _sample_sparse_frames(row, frames_per_video)
            if not frames:
                continue
            frame_feats = _normalize(encode_images(clip_bundle, frames, batch_size=batch_size))

            age_frame_scores, age_scores = _group_scores(frame_feats, age_prompts)
            person_frame_scores, person_scores = _group_scores(frame_feats, person_prompts)
            action_frame_scores, action_scores = _group_scores(frame_feats, action_prompts)
            scene_frame_scores, scene_scores = _group_scores(frame_feats, scene_prompts)

            age_label, age_conf = _top_label(age_scores, age_labels)
            person_label, person_conf = _top_label(person_scores, person_labels)
            scene_label, scene_conf = _top_label(scene_scores, scene_labels)

            action_sequence = []
            for frame_idx, scores in enumerate(action_frame_scores):
                label, confidence = _top_label(scores, action_labels)
                action_sequence.append({
                    "frame_index": frame_idx,
                    "action": label,
                    "confidence": round(confidence, 6),
                })

            top_actions = sorted(
                [
                    {"action": label, "score": round(float(score), 6)}
                    for label, score in zip(action_labels, action_scores)
                ],
                key=lambda item: item["score"],
                reverse=True,
            )[:5]

            payload = {
                "schema_version": "multiframe_alignment_teacher_v1",
                "video_id": row["video_id"],
                "segment_id": row["segment_id"],
                "video_path": row["video_path"],
                "frames": len(frames),
                "visual_attributes": {
                    "age_group": age_label,
                    "age_confidence": round(age_conf, 6),
                    "person_type": person_label,
                    "person_confidence": round(person_conf, 6),
                    "scene": scene_label,
                    "scene_confidence": round(scene_conf, 6),
                },
                "actions": top_actions,
                "action_sequence": action_sequence,
                "notes": [
                    "CLIP zero-shot pseudo labels; use as soft alignment evidence, not ground-truth demographics.",
                    "Action sequence is frame-order pseudo evidence from sparse sampled frames.",
                ],
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(f"[OK] wrote multiframe alignment teacher: {out_path} ({len(rows)} planned videos)")
    if target_video_ids:
        print(json.dumps({
            "target_filter": {
                "requested_video_ids": len(target_video_ids),
                "matched_manifest_rows": len(rows),
                "include_teacher_targets": include_teacher_targets,
                "max_query_rows": max_query_rows,
            }
        }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build lightweight multi-frame alignment teacher signals.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--frames_per_video", type=int, default=6)
    parser.add_argument("--max_videos", type=int, default=1000)
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--queries", action="append", default=[])
    parser.add_argument("--teacher_supervision", type=str, default="")
    parser.add_argument("--max_query_rows", type=int, default=0)
    parser.add_argument("--include_teacher_targets", action="store_true")
    args = parser.parse_args()
    build_alignment_teacher(
        manifest_name=args.manifest,
        out=args.out,
        frames_per_video=args.frames_per_video,
        max_videos=args.max_videos,
        model_name=args.model_name,
        pretrained=args.pretrained,
        batch_size=args.batch_size,
        queries=args.queries,
        teacher_supervision=args.teacher_supervision,
        max_query_rows=args.max_query_rows,
        include_teacher_targets=args.include_teacher_targets,
    )


if __name__ == "__main__":
    main()
