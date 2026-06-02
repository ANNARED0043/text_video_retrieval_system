import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Paths:
    project_root: Path
    data_dir: Path
    raw_videos_dir: Path
    manifests_dir: Path


@dataclass
class Config:
    # segmentation
    fixed_segment_seconds: float = 2.0
    fixed_fps: int = 2  # only for preview/feature stage, not needed in Phase1

    # shot detection (PySceneDetect)
    shot_threshold: float = 27.0  # content detector threshold, tune later

    paths: Paths = None


def load_config() -> Config:
    root = Path(__file__).resolve().parents[1]  # project_root/src/../
    data_dir = root / "data"
    paths = Paths(
        project_root=root,
        data_dir=data_dir,
        raw_videos_dir=data_dir / "raw_videos",
        manifests_dir=data_dir / "manifests",
    )
    cfg = Config(paths=paths)
    os.makedirs(paths.manifests_dir, exist_ok=True)
    return cfg