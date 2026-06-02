# （一键生成两种切分的 manifest）

from __future__ import annotations
import os
from pathlib import Path
from tqdm import tqdm

from src.config import load_config
from src.data.segmenter_fixed import fixed_window_segments
from src.data.segmenter_shot import shot_based_segments
from src.data.manifest_writer import write_jsonl, segment_to_manifest_row


def infer_video_id(video_path: Path) -> str:
    return video_path.stem


def main():
    cfg = load_config()
    raw_dir = cfg.paths.raw_videos_dir
    videos = sorted([p for p in raw_dir.glob("*.mp4")])

    if not videos:
        raise RuntimeError(
            f"No .mp4 found in {raw_dir}. Put a demo video at data/raw_videos/demo.mp4"
        )

    fixed_rows = []
    shot_rows = []

    for vp in tqdm(videos, desc="Segmenting videos"):
        video_id = infer_video_id(vp)
        vp_str = str(vp.as_posix())

        fixed_segs = fixed_window_segments(vp_str, video_id=video_id, window_sec=cfg.fixed_segment_seconds)
        for s in fixed_segs:
            fixed_rows.append(segment_to_manifest_row(s, video_path=vp_str, strategy="fixed"))

        shot_segs = shot_based_segments(vp_str, video_id=video_id, threshold=cfg.shot_threshold)
        for s in shot_segs:
            shot_rows.append(segment_to_manifest_row(s, video_path=vp_str, strategy="shot"))

    fixed_out = cfg.paths.manifests_dir / "segments_fixed.jsonl"
    shot_out = cfg.paths.manifests_dir / "segments_shot.jsonl"

    write_jsonl(fixed_rows, str(fixed_out))
    write_jsonl(shot_rows, str(shot_out))

    print(f"[OK] fixed manifest: {fixed_out}  ({len(fixed_rows)} segments)")
    print(f"[OK] shot  manifest: {shot_out}  ({len(shot_rows)} segments)")


if __name__ == "__main__":
    # Ensure src is importable when running as a script
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1]))
    main()