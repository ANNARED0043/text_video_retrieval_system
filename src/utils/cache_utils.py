# 先做通用缓存，后面 rewrite / rerank / explain 都能用。

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_cache_key(payload: dict) -> str:
    text = stable_json_dumps(payload)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_path(cache_dir: str | Path, key: str) -> Path:
    d = ensure_dir(cache_dir)
    return d / f"{key}.json"


def load_json_cache(cache_dir: str | Path, key: str) -> dict | None:
    p = cache_path(cache_dir, key)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_cache(cache_dir: str | Path, key: str, data: dict) -> Path:
    p = cache_path(cache_dir, key)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return p