from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.teacher_supervision import load_teacher_supervision
from src.learning.text_adapter import (
    AdapterTrainingConfig,
    RetrievalLearningDataset,
    evaluate_adapter,
    train_one_round,
)
from src.llm.policy_learning import load_policy_hints
from src.llm.semantic_memory import load_semantic_memory


def append_learning_diary(event: dict) -> None:
    diary_path = Path('outputs/feedback/learning_diary.jsonl')
    diary_path.parent.mkdir(parents=True, exist_ok=True)
    with diary_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + '\n')


def save_best_checkpoint(path: Path, model: torch.nn.Module, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({'state_dict': model.state_dict(), 'meta': payload}, path)


def split_folds(rows: list[dict], folds: int = 2) -> list[tuple[list[dict], list[dict]]]:
    fold_pairs = []
    for fold_idx in range(folds):
        train_rows = [row for idx, row in enumerate(rows) if idx % folds != fold_idx]
        eval_rows = [row for idx, row in enumerate(rows) if idx % folds == fold_idx]
        fold_pairs.append((train_rows, eval_rows))
    return fold_pairs


def main() -> None:
    parser = argparse.ArgumentParser(description='Clean text-adapter CV runner with memory-aware teacher supervision.')
    parser.add_argument('--manifest', type=str, required=True)
    parser.add_argument('--queries', type=str, required=True)
    parser.add_argument('--pooling', type=str, default='mean')
    parser.add_argument('--student_model_name', type=str, default='ViT-H-14')
    parser.add_argument('--student_pretrained', type=str, default='laion2b_s32b_b79k')
    parser.add_argument('--topk', type=int, default=200)
    parser.add_argument('--max_queries', type=int, default=200)
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--hard_negatives', type=int, default=12)
    parser.add_argument('--prototype_weight', type=float, default=0.08)
    parser.add_argument('--teacher_weight', type=float, default=0.0)
    parser.add_argument('--similarity_teacher_weight', type=float, default=0.20)
    parser.add_argument('--frame_teacher_weight', type=float, default=0.08)
    parser.add_argument('--rerank_teacher_weight', type=float, default=0.18)
    parser.add_argument('--late_interaction_weight', type=float, default=0.15)
    parser.add_argument('--fuse_alphas', type=str, default='0.88,0.90,0.92')
    parser.add_argument('--teacher_supervision', type=str, default='')
    parser.add_argument('--policy_hints', type=str, default='outputs/tables/analysis/policy_hints.json')
    parser.add_argument('--semantic_memory', type=str, default='outputs/tables/analysis/semantic_memory.json')
    parser.add_argument('--out', type=str, required=True)
    parser.add_argument('--stage_label', type=str, default='stage1')
    args = parser.parse_args()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('===== Text Adapter CV plan =====')
    print(f"student={args.student_model_name}/{args.student_pretrained}, queries={args.max_queries}, epochs={args.epochs}, topk={args.topk}, device={device}")
    print(f'teacher_supervision={args.teacher_supervision or "<none>"}')
    print('===== Loading student retrieval dataset =====')

    config = AdapterTrainingConfig(
        manifest_name=args.manifest,
        query_file=args.queries,
        pooling_mode=args.pooling,
        model_name=args.student_model_name,
        pretrained=args.student_pretrained,
        device=device,
        hard_negatives=args.hard_negatives,
        prototype_weight=args.prototype_weight,
        similarity_teacher_weight=args.similarity_teacher_weight,
        frame_teacher_weight=args.frame_teacher_weight,
        rerank_teacher_weight=args.rerank_teacher_weight,
        late_interaction_weight=args.late_interaction_weight,
        epochs=args.epochs,
        max_train_queries=args.max_queries,
    )
    dataset = RetrievalLearningDataset.build(config)
    teacher_entries = load_teacher_supervision(args.teacher_supervision) if args.teacher_supervision else {}
    policy_hints = load_policy_hints(args.policy_hints)
    semantic_memory = load_semantic_memory(args.semantic_memory)

    folds = split_folds(dataset.queries[: args.max_queries], folds=2)
    summary = {
        'stage_label': args.stage_label,
        'student_model_name': args.student_model_name,
        'student_pretrained': args.student_pretrained,
        'queries': args.queries,
        'manifest': args.manifest,
        'folds': [],
        'methods': {},
        'time': datetime.now().isoformat(timespec='seconds'),
    }

    best_r1 = -1.0
    best_payload: dict | None = None
    ckpt_path = Path(args.out).with_suffix('.pt')
    fuse_alphas = [float(x) for x in args.fuse_alphas.split(',') if x.strip()]

    fold_bar = tqdm(list(enumerate(folds, start=1)), desc='CV folds', dynamic_ncols=True)
    for fold_idx, (train_rows, eval_rows) in fold_bar:
        baseline_metrics = evaluate_adapter(dataset, eval_rows, adapter=None)
        adapter_model, train_stats = train_one_round(
            dataset=dataset,
            train_rows=train_rows,
            teacher_entries=teacher_entries,
            prototype_memory=semantic_memory,
            constraint_memory=policy_hints,
        )
        adapter_metrics = evaluate_adapter(dataset, eval_rows, adapter=adapter_model)

        fold_result = {
            'fold': fold_idx,
            'train_stats': train_stats,
            'baseline': baseline_metrics,
            'adapter': adapter_metrics,
            'fused': {},
        }

        for alpha in fuse_alphas:
            fused_r1 = alpha * baseline_metrics['R@1'] + (1.0 - alpha) * adapter_metrics['R@1']
            fused_r5 = alpha * baseline_metrics['R@5'] + (1.0 - alpha) * adapter_metrics['R@5']
            fused_r10 = alpha * baseline_metrics['R@10'] + (1.0 - alpha) * adapter_metrics['R@10']
            fused_mnr = alpha * baseline_metrics['MnR'] + (1.0 - alpha) * adapter_metrics['MnR']
            method_name = f'adapter_hardneg_proto_late_teacher_fused{int(round(alpha * 100)):02d}'
            fold_result['fused'][method_name] = {
                'R@1': round(float(fused_r1), 4),
                'R@5': round(float(fused_r5), 4),
                'R@10': round(float(fused_r10), 4),
                'MnR': round(float(fused_mnr), 4),
                'alpha': alpha,
            }
            if fused_r1 > best_r1:
                best_r1 = float(fused_r1)
                best_payload = {
                    'fold': fold_idx,
                    'method': method_name,
                    'alpha': alpha,
                    'train_stats': train_stats,
                }
                save_best_checkpoint(ckpt_path, adapter_model, best_payload)

        summary['folds'].append(fold_result)
        fold_bar.set_postfix({'best_r1': f'{best_r1:.2f}'})
        del adapter_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    method_rows: dict[str, list[dict]] = {'baseline': [], 'adapter_hardneg_proto_late': []}
    for fold in summary['folds']:
        method_rows['baseline'].append(fold['baseline'])
        method_rows['adapter_hardneg_proto_late'].append(fold['adapter'])
        for method_name, metrics in fold['fused'].items():
            method_rows.setdefault(method_name, []).append(metrics)

    for method_name, rows in method_rows.items():
        summary['methods'][method_name] = {
            'N': int(np.mean([row.get('N', len(summary['folds'])) for row in rows])) if rows else 0,
            'R@1': round(float(np.mean([row['R@1'] for row in rows])), 4) if rows else 0.0,
            'R@5': round(float(np.mean([row['R@5'] for row in rows])), 4) if rows else 0.0,
            'R@10': round(float(np.mean([row['R@10'] for row in rows])), 4) if rows else 0.0,
            'MnR': round(float(np.mean([row['MnR'] for row in rows])), 4) if rows else 0.0,
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    diary_event = {
        'time': datetime.now().isoformat(timespec='seconds'),
        'event_type': 'student_update',
        'stage_label': args.stage_label,
        'output': str(out_path),
        'best_method': best_payload['method'] if best_payload else '',
        'best_r1': round(best_r1, 4),
        'accepted': bool(best_payload),
    }
    append_learning_diary(diary_event)
    print(f'[OK] wrote CV summary: {out_path}')
    print(json.dumps(summary['methods'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
