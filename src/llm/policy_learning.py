from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def learn_policy_hints(rows: list[dict[str, Any]]) -> dict[str, Any]:
    strong = Counter()
    conservative = Counter()
    dense = Counter()
    expand = Counter()

    for row in rows:
        query = str(row.get("query", "")).lower()
        rank = int(row.get("rank", row.get("gt_rank", 9999)))
        if any(token in query for token in ("group", "crowd", "many", "two", "three")):
            expand["count"] += 1
        if any(token in query for token in ("boy", "girl", "child", "mother", "father")):
            dense["age"] += 1
            conservative["age"] += 1
        if any(token in query for token in ("kitchen", "room", "park", "stage")):
            dense["scene"] += 1
        if rank > 10:
            dense["generic"] += 1
            expand["generic"] += 1
        elif rank <= 3:
            strong["generic"] += 1

    return {
        "prefer_strong_rewrite_categories": [name for name, _ in strong.most_common()],
        "prefer_conservative_rewrite_categories": [name for name, _ in conservative.most_common()],
        "prefer_dense_categories": [name for name, _ in dense.most_common()],
        "prefer_expand_categories": [name for name, _ in expand.most_common()],
    }


def write_policy_hints(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_policy_hints(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}
