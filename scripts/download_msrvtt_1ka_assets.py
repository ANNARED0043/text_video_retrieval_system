from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlretrieve

ASSETS = {
    "msrvtt_test_1k.json": "https://huggingface.co/datasets/friedrichor/MSR-VTT/resolve/main/msrvtt_test_1k.json?download=true",
    "MSRVTT_data.json": "https://huggingface.co/datasets/friedrichor/MSR-VTT/resolve/main/raw_data/MSRVTT_data.json?download=true",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out_dir",
        type=str,
        default="data/annotations/msrvtt",
        help="Directory to store downloaded annotation files.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, url in ASSETS.items():
        target = out_dir / name
        print(f"downloading {url} -> {target}")
        urlretrieve(url, target)
        print(f"done: {target}")


if __name__ == "__main__":
    main()
