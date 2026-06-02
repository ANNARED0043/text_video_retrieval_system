from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TeacherTarget:
    video_id: str
    score: float


@dataclass
class TeacherSupervisionEntry:
    qid: int | str
    query: str
    gt_video_id: str
    source: str = "unknown"
    similarity_targets: list[TeacherTarget] = field(default_factory=list)
    listwise_targets: list[TeacherTarget] = field(default_factory=list)
    hard_negatives: list[str] = field(default_factory=list)
    frame_relevance: list[float] = field(default_factory=list)
    prototype_terms: list[str] = field(default_factory=list)
    structured_prototypes: dict[str, list[str]] = field(default_factory=dict)
    constraint_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "qid": self.qid,
            "query": self.query,
            "gt_video_id": self.gt_video_id,
            "source": self.source,
            "similarity_targets": [target.__dict__ for target in self.similarity_targets],
            "listwise_targets": [target.__dict__ for target in self.listwise_targets],
            "hard_negatives": self.hard_negatives,
            "frame_relevance": self.frame_relevance,
            "prototype_terms": self.prototype_terms,
            "structured_prototypes": self.structured_prototypes,
            "constraint_tags": self.constraint_tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "TeacherSupervisionEntry":
        return cls(
            qid=row.get("qid", ""),
            query=row.get("query", ""),
            gt_video_id=row.get("gt_video_id", ""),
            source=row.get("source", "unknown"),
            similarity_targets=[
                TeacherTarget(video_id=str(target.get("video_id", "")), score=float(target.get("score", 0.0)))
                for target in row.get("similarity_targets", [])
                if target.get("video_id")
            ],
            listwise_targets=[
                TeacherTarget(video_id=str(target.get("video_id", "")), score=float(target.get("score", 0.0)))
                for target in row.get("listwise_targets", [])
                if target.get("video_id")
            ],
            hard_negatives=[str(video_id) for video_id in row.get("hard_negatives", []) if video_id],
            frame_relevance=[float(x) for x in row.get("frame_relevance", [])],
            prototype_terms=[str(term) for term in row.get("prototype_terms", []) if term],
            structured_prototypes={
                str(key): [str(term) for term in values if term]
                for key, values in dict(row.get("structured_prototypes", {})).items()
            },
            constraint_tags=[str(tag) for tag in row.get("constraint_tags", []) if tag],
            metadata=dict(row.get("metadata", {})),
        )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def load_teacher_supervision(path: str | Path) -> dict[str, TeacherSupervisionEntry]:
    file_path = Path(path)
    entries: dict[str, TeacherSupervisionEntry] = {}
    for row in _read_jsonl(file_path):
        entry = TeacherSupervisionEntry.from_dict(row)
        entries[str(entry.qid)] = entry
    return entries


def write_teacher_supervision(path: str | Path, entries: list[TeacherSupervisionEntry]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")


def entry_for_query(
    teacher_entries: dict[str, TeacherSupervisionEntry],
    qid: int | str,
) -> TeacherSupervisionEntry | None:
    return teacher_entries.get(str(qid))


def compact_topk_targets(
    targets: list[TeacherTarget],
    topk: int,
    drop_nonpositive: bool = True,
) -> list[TeacherTarget]:
    ranked = sorted(targets, key=lambda item: item.score, reverse=True)
    if drop_nonpositive:
        ranked = [item for item in ranked if item.score > 0]
    return ranked[:topk]
