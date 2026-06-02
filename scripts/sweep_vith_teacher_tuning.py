from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SWEEP_CONFIGS = [
    {
        'name': 'tune_a_balanced',
        'similarity_teacher_weight': 0.20,
        'frame_teacher_weight': 0.08,
        'rerank_teacher_weight': 0.18,
        'late_interaction_weight': 0.15,
        'fuse_alphas': '0.88,0.90,0.92',
    },
    {
        'name': 'tune_b_conservative',
        'similarity_teacher_weight': 0.18,
        'frame_teacher_weight': 0.05,
        'rerank_teacher_weight': 0.12,
        'late_interaction_weight': 0.10,
        'fuse_alphas': '0.90,0.92,0.94',
    },
    {
        'name': 'tune_c_soft',
        'similarity_teacher_weight': 0.16,
        'frame_teacher_weight': 0.04,
        'rerank_teacher_weight': 0.10,
        'late_interaction_weight': 0.08,
        'fuse_alphas': '0.88,0.90,0.92',
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description='Sweep stage teacher/memory weights with resume.')
    parser.add_argument('--teacher_supervision', type=str, required=True)
    parser.add_argument('--out_dir', type=str, required=True)
    parser.add_argument('--max_queries', type=int, default=200)
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--topk', type=int, default=200)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / 'summary.json'

    sweep_bar = tqdm(SWEEP_CONFIGS, desc='ViT-H teacher sweep', dynamic_ncols=True)
    results = []
    for config in sweep_bar:
        out_file = out_dir / f"{config['name']}.json"
        if out_file.exists() and not args.overwrite:
            payload = json.loads(out_file.read_text(encoding='utf-8'))
            results.append(payload)
            sweep_bar.set_postfix({'current': config['name'], 'winner': payload.get('winner', '')})
            continue

        cmd = [
            sys.executable, '-u', 'scripts/train_text_adapter_cv.py',
            '--manifest', 'msrvtt_fixed_1kA.jsonl',
            '--queries', 'msrvtt_1kA_test_queries.jsonl',
            '--pooling', 'mean',
            '--student_model_name', 'ViT-H-14',
            '--student_pretrained', 'laion2b_s32b_b79k',
            '--topk', str(args.topk),
            '--max_queries', str(args.max_queries),
            '--epochs', str(args.epochs),
            '--hard_negatives', '12',
            '--prototype_weight', '0.08',
            '--teacher_weight', '0.0',
            '--similarity_teacher_weight', str(config['similarity_teacher_weight']),
            '--frame_teacher_weight', str(config['frame_teacher_weight']),
            '--rerank_teacher_weight', str(config['rerank_teacher_weight']),
            '--late_interaction_weight', str(config['late_interaction_weight']),
            '--fuse_alphas', config['fuse_alphas'],
            '--teacher_supervision', args.teacher_supervision,
            '--out', str(out_file),
            '--stage_label', config['name'],
        ]
        subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
        payload = json.loads(out_file.read_text(encoding='utf-8'))
        best_method = max(payload['methods'].items(), key=lambda item: item[1]['R@1'])[0]
        payload['winner'] = best_method
        out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        results.append(payload)
        sweep_bar.set_postfix({'current': config['name'], 'winner': best_method})

    summary = {
        'runs': [
            {
                'name': payload.get('stage_label', ''),
                'winner': max(payload['methods'].items(), key=lambda item: item[1]['R@1'])[0],
                'best_r1': max(payload['methods'].values(), key=lambda item: item['R@1'])['R@1'],
            }
            for payload in results
        ]
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[OK] wrote sweep summary: {summary_path}')


if __name__ == '__main__':
    main()
