from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.teacher_supervision import TeacherSupervisionEntry, TeacherTarget, write_teacher_supervision
from src.llm.semantic_memory import derive_constraint_tags


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _extract_targets(row: dict, key_candidates: list[str], topn: int) -> list[TeacherTarget]:
    for key in key_candidates:
        value = row.get(key)
        if isinstance(value, list):
            targets = []
            for item in value[:topn]:
                if isinstance(item, dict) and item.get('video_id'):
                    targets.append(TeacherTarget(video_id=str(item['video_id']), score=float(item.get('score', 0.0))))
                elif isinstance(item, list) and len(item) >= 2:
                    targets.append(TeacherTarget(video_id=str(item[0]), score=float(item[1])))
                elif isinstance(item, str):
                    targets.append(TeacherTarget(video_id=item, score=float(topn - len(targets))))
            if targets:
                return targets
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description='Build compact teacher supervision JSONL from rerank or teacher logs.')
    parser.add_argument('--rerank_log', type=str, required=True)
    parser.add_argument('--topn', type=int, default=20)
    parser.add_argument('--retrieval_topn', type=int, default=20)
    parser.add_argument('--out', type=str, required=True)
    parser.add_argument('--source', type=str, default='vic_style_rerank')
    args = parser.parse_args()

    rows = _read_jsonl(Path(args.rerank_log))
    entries: list[TeacherSupervisionEntry] = []
    for idx, row in enumerate(rows):
        query = str(row.get('query', ''))
        gt_video_id = str(row.get('gt_video_id', row.get('video_id', '')))
        similarity_targets = _extract_targets(
            row,
            ['retrieval_topk', 'retrieval_results', 'retrieval_candidates', 'baseline_topk', 'topk'],
            args.retrieval_topn,
        )
        listwise_targets = _extract_targets(
            row,
            ['rerank_topk', 'reranked_results', 'rerank_results', 'topk', 'candidates'],
            args.topn,
        )
        hard_negatives = [target.video_id for target in listwise_targets if target.video_id != gt_video_id][: min(10, len(listwise_targets))]
        prototype_terms = [token for token in query.lower().split() if len(token) >= 4][:10]
        entries.append(
            TeacherSupervisionEntry(
                qid=row.get('qid', idx),
                query=query,
                gt_video_id=gt_video_id,
                source=args.source,
                similarity_targets=similarity_targets,
                listwise_targets=listwise_targets,
                hard_negatives=hard_negatives,
                frame_relevance=[1.0 if gt_video_id else 0.0],
                prototype_terms=prototype_terms,
                constraint_tags=derive_constraint_tags(query),
                metadata={'from_log': Path(args.rerank_log).name},
            )
        )

    write_teacher_supervision(args.out, entries)
    print(f'[OK] wrote teacher supervision: {args.out} ({len(entries)} rows)')


if __name__ == '__main__':
    main()
