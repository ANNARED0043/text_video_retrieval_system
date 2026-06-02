from __future__ import annotations
import cv2
import numpy as np


def get_video_duration_seconds(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()

    if fps is None or fps <= 0:
        # fallback: unknown fps
        raise RuntimeError(f"Invalid FPS for video: {video_path}")
    return float(frame_count / fps)


def sample_frames(video_path: str, start_sec: float, end_sec: float, fps: int = 2) -> list[np.ndarray]:
    """
    Uniformly sample frames in [start_sec, end_sec) at a fixed fps.
    Returns list of RGB uint8 frames.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps is None or video_fps <= 0:
        cap.release()
        raise RuntimeError(f"Invalid FPS for video: {video_path}")

    frames = []
    # sample timestamps
    step = 1.0 / float(fps)
    t = start_sec
    while t < end_sec:
        frame_idx = int(t * video_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        frames.append(rgb)
        t += step

    cap.release()
    return frames