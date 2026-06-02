from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _append_diary(event: dict) -> None:
    diary = Path('outputs/feedback/learning_diary.jsonl')
    diary.parent.mkdir(parents=True, exist_ok=True)
    with diary.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + '\n')


def _stage_policy(stage: int) -> dict:
    common = {
        'quick_gate': '1kA 200-query',
        'promotion_gate': 'full 1kA',
        'teacher_cache_keep': ['top-k soft labels', 'frame relevance', 'hard negatives'],
        'round_keep': ['best checkpoint', 'summary json', 'diary entry', 'ablation row'],
    }
    if stage == 1:
        return {
            **common,
            'stage_label': 'stage1',
            'main_teacher_target': 'ViCLIP',
            'techniques': [
                'similarity distillation',
                'hard negative mining',
                'prototype-aware learning',
                'constraint-memory-assisted sampling',
                'teacher soft label learning',
            ],
        }
    if stage == 2:
        return {
            **common,
            'stage_label': 'stage2',
            'main_teacher_target': 'ViCLIP',
            'techniques': [
                'frame relevance teacher',
                'late interaction teacher',
                'ViC-style top-20 listwise soft labels',
            ],
        }
    return {
        **common,
        'stage_label': 'stage3',
        'main_teacher_target': 'ViCLIP',
        'techniques': [
            'prototype memory',
            'hard negative memory',
            'constraint memory',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Run staged agent learning bootstrap steps with cache-aware outputs.')
    parser.add_argument('--stage', type=int, choices=[1, 2, 3], required=True)
    parser.add_argument('--teacher_supervision', type=str, default='outputs/tables/analysis/teacher_supervision_vicstyle_top10.jsonl')
    parser.add_argument('--out_dir', type=str, default='outputs/tables/analysis/agent_learning_rounds')
    parser.add_argument('--max_queries', type=int, default=200)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    policy = _stage_policy(args.stage)

    if args.stage == 1:
        subprocess.run([sys.executable, 'scripts/prepare_msrvtt_train9k.py'], check=True, cwd=str(PROJECT_ROOT))
        _append_diary({
            'time': datetime.now().isoformat(timespec='seconds'),
            'event_type': 'stage_start',
            'stage': 1,
            'stage_label': policy['stage_label'],
            'note': 'Prepared clean train_9k list and query file.',
            'policy': policy,
        })
        print('[OK] stage 1 bootstrap complete')
        return

    if args.stage == 2:
        stage_out = out_dir / 'stage2_cv.json'
        subprocess.run([
            sys.executable, '-u', 'scripts/train_text_adapter_cv.py',
            '--manifest', 'msrvtt_fixed_1kA.jsonl',
            '--queries', 'msrvtt_1kA_test_queries.jsonl',
            '--pooling', 'mean',
            '--student_model_name', 'ViT-H-14',
            '--student_pretrained', 'laion2b_s32b_b79k',
            '--max_queries', str(args.max_queries),
            '--teacher_supervision', args.teacher_supervision,
            '--out', str(stage_out),
            '--stage_label', policy['stage_label'],
        ], check=True, cwd=str(PROJECT_ROOT))
        _append_diary({
            'time': datetime.now().isoformat(timespec='seconds'),
            'event_type': 'stage_start',
            'stage': 2,
            'stage_label': policy['stage_label'],
            'output': str(stage_out),
            'policy': policy,
        })
        print('[OK] stage 2 bootstrap complete')
        return

    memory_report = out_dir / 'stage3_memory_refresh.json'
    payload = {
        'time': datetime.now().isoformat(timespec='seconds'),
        'prototype_memory': 'active',
        'hard_negative_memory': 'active',
        'constraint_memory': 'active',
        'policy': policy,
    }
    memory_report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    _append_diary({
        'time': payload['time'],
        'event_type': 'stage_start',
        'stage': 3,
        'stage_label': policy['stage_label'],
        'output': str(memory_report),
        'policy': policy,
    })
    print('[OK] stage 3 bootstrap complete')


if __name__ == '__main__':
    main()
