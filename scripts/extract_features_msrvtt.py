from __future__ import annotations
import os
from pathlib import Path
from scripts.extract_features import main as extract_main

if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1]))
    extract_main(
        manifest_name="msrvtt_fixed.jsonl",
        pooling_mode="mean",
        sample_fps=2,
        batch_size=32,
    )