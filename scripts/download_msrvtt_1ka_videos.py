from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from tqdm import tqdm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ann", type=str, default="data/annotations/msrvtt/msrvtt_test_1k.json")
    parser.add_argument("--out_dir", type=str, default="data/raw_videos/msrvtt")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    ann_path = Path(args.ann)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = json.loads(ann_path.read_text(encoding='utf-8'))
    if args.limit > 0:
        rows = rows[:args.limit]

    for row in tqdm(rows, desc="Download MSR-VTT 1kA videos", dynamic_ncols=True):
        target = out_dir / f"{row['video_id']}.mp4"
        if target.exists():
            continue
        cmd = [
            'yt-dlp',
            row['url'],
            '-o',
            str(target),
            '--download-sections',
            f"*{row['start time']}-{row['end time']}",
            '--force-keyframes-at-cuts',
            '--merge-output-format',
            'mp4',
        ]
        subprocess.run(cmd, check=False)


if __name__ == '__main__':
    main()
