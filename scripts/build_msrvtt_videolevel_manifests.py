from __future__ import annotations

import json
import sys
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.utils.video_utils import get_video_duration_seconds


def _read_vid_list(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _manifest_row(video_path: Path) -> dict:
    duration = float(get_video_duration_seconds(str(video_path)))
    video_id = video_path.stem
    return {
        "video_id": video_id,
        "segment_id": f"{video_id}_seg0000",
        "video_path": str(video_path.resolve().as_posix()),
        "start_sec": 0.0,
        "end_sec": duration,
        "strategy": "video_level",
        "duration_sec": duration,
    }


def main() -> None:
    cfg = load_config()
    root = cfg.paths.project_root
    ann_dir = cfg.paths.data_dir / "annotations" / "msrvtt"
    manifests_dir = cfg.paths.manifests_dir
    raw_dir = cfg.paths.raw_videos_dir / "msrvtt"

    val_list = ann_dir / "val_list_jsfusion.txt"
    if not raw_dir.exists():
        raise RuntimeError(f"Missing raw video directory: {raw_dir}")
    if not val_list.exists():
        raise RuntimeError(f"Missing 1kA video list: {val_list}")

    keep_1ka = _read_vid_list(val_list)
    videos = sorted(raw_dir.glob("*.mp4"))
    if not videos:
        raise RuntimeError(f"No mp4 files found in: {raw_dir}")

    full_rows = []
    rows_1ka = []
    for video_path in tqdm(videos, desc="Build MSRVTT video-level manifest", dynamic_ncols=True):
        row = _manifest_row(video_path)
        full_rows.append(row)
        if row["video_id"] in keep_1ka:
            rows_1ka.append(row)

    manifests_dir.mkdir(parents=True, exist_ok=True)
    full_out = manifests_dir / "msrvtt_fixed.jsonl"
    oneka_out = manifests_dir / "msrvtt_fixed_1kA.jsonl"
    full_out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in full_rows) + "\n",
        encoding="utf-8",
    )
    oneka_out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows_1ka) + "\n",
        encoding="utf-8",
    )

    print(f"[OK] wrote full video-level manifest: {full_out} ({len(full_rows)} rows)")
    print(f"[OK] wrote 1kA video-level manifest: {oneka_out} ({len(rows_1ka)} rows)")


if __name__ == "__main__":
    main()
