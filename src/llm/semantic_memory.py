from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_FOCUS_TERMS = {
    "age": ["boy", "girl", "child", "kid", "baby", "man", "woman"],
    "count": ["one", "single", "two", "three", "group", "crowd"],
    "relation": ["mother", "father", "son", "daughter", "friend", "couple"],
    "scene": ["room", "kitchen", "street", "park", "stage", "outdoor", "indoor"],
    "object": ["dog", "cat", "car", "ball", "guitar", "phone"],
}

ACTION_TERMS = {
    "run", "running", "walk", "walking", "dance", "dancing", "sing", "singing",
    "talk", "talking", "cook", "cooking", "play", "playing", "drive", "driving",
    "ride", "riding", "swim", "swimming", "jump", "jumping", "eat", "eating",
    "drink", "drinking", "cut", "cutting", "open", "opening", "close", "closing",
    "hold", "holding", "throw", "throwing", "kick", "kicking", "laugh", "laughing",
    "stir", "stirring", "shoot", "shooting", "read", "reading", "write", "writing",
    "exercise", "exercising", "climb", "climbing", "fall", "falling", "sit", "sitting",
    "stand", "standing", "wash", "washing", "clean", "cleaning", "dress", "dressing",
    "perform", "performing", "interview", "interviewing", "speak", "speaking",
    "show", "showing", "demonstrate", "demonstrating", "mix", "mixing", "pour", "pouring",
}

OBJECT_TERMS = {
    "dog", "cat", "car", "ball", "guitar", "phone", "bike", "bicycle", "motorcycle",
    "horse", "food", "drink", "table", "chair", "book", "computer", "baby", "child",
    "man", "woman", "person", "people", "shirt", "hat", "cup", "bottle", "camera",
    "boy", "girl", "teenager", "kid", "elderly", "group", "couple", "basketball",
    "stroller", "cart", "knife", "pan", "pot", "drum", "piano", "microphone",
    "screen", "television", "tv", "vehicle", "road", "bike", "helmet", "uniform",
}

SCENE_TERMS = {
    "room", "kitchen", "street", "park", "stage", "outdoor", "indoor", "beach",
    "office", "home", "house", "yard", "field", "court", "water", "pool", "restaurant",
    "store", "school", "gym", "road", "city",
    "stadium", "court", "field", "news", "studio", "bedroom", "bathroom", "garage",
    "snow", "mountain", "garden", "market", "classroom", "concert",
}

RELATION_TERMS = {
    "mother", "father", "son", "daughter", "friend", "friends", "couple",
    "group", "team", "interviewer", "candidate", "teacher", "student",
    "child", "parent", "family", "people", "person", "man", "woman",
    "boy", "girl", "crowd", "audience",
}

STOPWORDS = {
    "the", "and", "with", "about", "there", "video", "clip", "are", "for",
    "from", "into", "while", "some", "something", "being", "their", "this",
    "that", "have", "has", "his", "her", "its", "your", "our", "them",
    "they", "you", "how", "what", "when", "where", "who", "talking", "talks",
}


def extract_query_tokens(query: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for raw in query.split():
        token = raw.strip(" ,.!?;:'\"()[]{}").lower()
        if len(token) < 3 or token in STOPWORDS or token.isdigit():
            continue
        if token not in seen:
            tokens.append(token)
            seen.add(token)
    return tokens


def extract_structured_prototypes(query: str) -> dict[str, list[str]]:
    tokens = extract_query_tokens(query)
    actions = [token for token in tokens if token in ACTION_TERMS]
    objects = [token for token in tokens if token in OBJECT_TERMS]
    scenes = [token for token in tokens if token in SCENE_TERMS]
    relations = [token for token in tokens if token in RELATION_TERMS]
    return {
        "action": actions[:3],
        "object": objects[:3],
        "scene": scenes[:3],
        "relation": relations[:3],
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_semantic_memory(path: str | Path) -> dict[str, Any]:
    return _read_json(Path(path))


def derive_constraint_tags(query: str) -> list[str]:
    tokens = set(extract_query_tokens(query))
    tags: list[str] = []
    for group_name, words in DEFAULT_FOCUS_TERMS.items():
        if any(word in tokens for word in words):
            tags.append(group_name)
    return tags


def matched_visual_guard_reasons(query: str, memory: dict[str, Any] | None = None) -> list[str]:
    tags = derive_constraint_tags(query)
    reasons = [f"learned_{tag}_guard" for tag in tags]
    if memory:
        focus_terms = set(memory.get("focus_terms", []))
        tokens = set(extract_query_tokens(query))
        if focus_terms.intersection(tokens):
            reasons.append("memory_dynamic_term_guard")
    return reasons


def build_semantic_memory_from_queries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tag_counter = Counter()
    prototype_counter = Counter()
    structured_counter = {
        "action": Counter(),
        "object": Counter(),
        "scene": Counter(),
        "relation": Counter(),
    }
    for row in rows:
        query = str(row.get("query", ""))
        gt_video_id = str(row.get("gt_video_id", ""))
        for tag in derive_constraint_tags(query):
            tag_counter[tag] += 1
        for token in extract_query_tokens(query):
            prototype_counter[f"query::{token}"] += 1
        structured = extract_structured_prototypes(query)
        for group_name, values in structured.items():
            for value in values:
                structured_counter[group_name][value] += 1
        if gt_video_id:
            prototype_counter[f"video::{gt_video_id}"] += 1

    return {
        "focus_terms": [name for name, count in tag_counter.most_common()],
        "prototypes": {name: {"count": count} for name, count in prototype_counter.most_common(100)},
        "structured_prototypes": {
            group_name: [name for name, _count in counter.most_common(50)]
            for group_name, counter in structured_counter.items()
        },
        "failure_signals": {name: count for name, count in tag_counter.items()},
    }


def write_semantic_memory(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
