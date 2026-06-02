from __future__ import annotations

from pathlib import Path
from typing import List
from typing import TYPE_CHECKING
from PIL import Image

from src.utils.cache_utils import make_cache_key, load_json_cache, save_json_cache
from src.utils.video_utils import sample_frames

if TYPE_CHECKING:
    from src.llm.client import OpenAIClient


CANDIDATE_SEMANTICS_VERSION = "v1"


def _save_frame(frame, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(frame, Image.Image):
        img = frame
    else:
        img = Image.fromarray(frame)
    img.save(out_path)
    return out_path


def _select_representative_frames(frames: List) -> List:
    if len(frames) <= 3:
        return frames
    idxs = [0, len(frames) // 2, len(frames) - 1]
    return [frames[i] for i in idxs]


def build_candidate_semantics_system_prompt() -> str:
    return (
        "You are summarizing a short video segment for retrieval reranking.\n"
        "Use only visible evidence from the frames.\n"
        "Do not invent details.\n"
        "Output exactly in this format:\n"
        "summary: <one short sentence>\n"
        "tags: <comma-separated visual tags>"
    )


def build_candidate_semantics_user_prompt() -> str:
    return (
        "Describe the visible action, scene, and salient objects in these frames.\n"
        "Keep the summary short and concrete.\n"
        "Do not speculate."
    )


def parse_candidate_semantics(text: str) -> dict:
    summary = ""
    tags = []

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        if low.startswith("summary:"):
            summary = ln.split(":", 1)[1].strip()
        elif low.startswith("tags:"):
            raw = ln.split(":", 1)[1].strip()
            tags = [x.strip() for x in raw.split(",") if x.strip()]

    return {
        "summary": summary,
        "tags": tags,
    }


def get_candidate_semantics_with_cache(
    candidate: dict,
    client: OpenAIClient,
    cache_dir: str | Path,
    tmp_frame_dir: str | Path,
) -> dict:
    """
    candidate must contain:
      video_id, segment_id, video_path, start_sec, end_sec
    """
    key_payload = {
        "task": "candidate_semantics",
        "model": client.model,
        "version": CANDIDATE_SEMANTICS_VERSION,
        "segment_id": candidate["segment_id"],
        "video_id": candidate["video_id"],
        "start_sec": round(float(candidate["start_sec"]), 3),
        "end_sec": round(float(candidate["end_sec"]), 3),
    }
    cache_key = make_cache_key(key_payload)

    cached = load_json_cache(cache_dir, cache_key)
    if cached is not None:
        cached["cache_hit"] = True
        return cached

    frames = sample_frames(
        candidate["video_path"],
        float(candidate["start_sec"]),
        float(candidate["end_sec"]),
        fps=1,
    )
    if len(frames) == 0:
        result = {
            "video_id": candidate["video_id"],
            "segment_id": candidate["segment_id"],
            "summary": "",
            "tags": [],
            "cache_hit": False,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        }
        save_json_cache(cache_dir, cache_key, result)
        return result

    selected = _select_representative_frames(frames)
    frame_paths = []
    tmp_frame_dir = Path(tmp_frame_dir)
    for idx, fr in enumerate(selected):
        out_path = tmp_frame_dir / f"{candidate['segment_id']}_{idx}.jpg"
        frame_paths.append(str(_save_frame(fr, out_path)))

    resp = client.generate_vision_text(
        system_prompt=build_candidate_semantics_system_prompt(),
        user_prompt=build_candidate_semantics_user_prompt(),
        image_paths=frame_paths,
        temperature=0.0,
        max_output_tokens=120,
    )
    parsed = parse_candidate_semantics(resp.text)

    result = {
        "video_id": candidate["video_id"],
        "segment_id": candidate["segment_id"],
        "summary": parsed["summary"],
        "tags": parsed["tags"],
        "cache_hit": False,
        "usage": {
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "total_tokens": resp.total_tokens,
        },
    }
    save_json_cache(cache_dir, cache_key, result)
    return result
