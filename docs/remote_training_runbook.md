# Remote Training Runbook

## Goal

Push the current `ViT-H-14/laion2b_s32b_b79k` baseline from the current quick
reference toward a stronger final result with staged learning on
`msrvtt_train_9k`, while using a leakage-safe dev split as the fast gate and
keeping full `1kA` as the locked promotion check.

## Current Storage Layout

- Full features:
  [data/features/msrvtt_fixed/mean/ViT-H-14_laion2b_s32b_b79k](E:/BISHE/video_retrieval_system/data/features/msrvtt_fixed/mean/ViT-H-14_laion2b_s32b_b79k)
- Full index:
  [data/indexes/msrvtt_fixed/mean/ViT-H-14_laion2b_s32b_b79k/flat_ip](E:/BISHE/video_retrieval_system/data/indexes/msrvtt_fixed/mean/ViT-H-14_laion2b_s32b_b79k/flat_ip)
- 1kA features:
  [data/features/msrvtt_fixed_1kA/mean/ViT-H-14_laion2b_s32b_b79k](E:/BISHE/video_retrieval_system/data/features/msrvtt_fixed_1kA/mean/ViT-H-14_laion2b_s32b_b79k)
- 1kA index:
  [data/indexes/msrvtt_fixed_1kA/mean/ViT-H-14_laion2b_s32b_b79k/flat_ip](E:/BISHE/video_retrieval_system/data/indexes/msrvtt_fixed_1kA/mean/ViT-H-14_laion2b_s32b_b79k/flat_ip)
- Learning diary:
  [outputs/feedback/learning_diary.jsonl](E:/BISHE/video_retrieval_system/outputs/feedback/learning_diary.jsonl)
- Technical notes:
  [docs/technical_stage_notes.md](E:/BISHE/video_retrieval_system/docs/technical_stage_notes.md)

## Acceptance Gate

Quick gate for each student update:

- run a leakage-safe dev quick eval
- require `R@1 > 48`
- require meaningful `R@5` and `R@10` gain over the current quick baseline

Promotion gate:

- if quick gate passes, run full `1kA`
- keep the student only if `train`, `val`, and full `1kA` all improve

Safety note:

- do not use the official `1kA test` split for hyperparameter search
- do not pick checkpoints based on repeated `1kA test` evaluation

If the gate fails:

- keep the summary and diary entry
- reject the student
- do not overwrite the current best checkpoint

## Stage Plan

### Stage 1

Train on `msrvtt_train_9k` with:

- similarity distillation
- hard negative mining
- prototype-aware learning
- constraint-memory-assisted sampling
- teacher soft label learning

Target:

- `R@1 47 -> 52~55`

### Stage 2

Add:

- frame relevance teacher
- late interaction teacher
- ViC-style top-20 listwise soft labels

Target:

- `R@1 52~55 -> 56~60`

### Stage 3

Refresh and reuse:

- prototype memory
- hard negative memory
- constraint memory

Target:

- stable acceptance-gated continual improvement

## Safety Rules

Teacher-side cache should keep only:

- top-k soft labels
- frame relevance
- hard negatives

Per round keep only:

- best checkpoint
- summary json
- diary entry
- ablation row

## Suggested Execution Order

1. Rebuild manifests
2. Extract full `msrvtt_fixed` features
3. Build full `msrvtt_fixed` index
4. Measure full `1kA` baseline candidate recall at `topk=30`
5. Run lightweight Stage 1 on baseline `topk30` candidates
6. Auto-run Stage 1 quick gate on `1kA 200-query`
7. If passed, run Stage 1 full `1kA`
8. Repeat the same pattern for Stage 2 and Stage 3

## Lightweight Stage 1 Command

Use this path first before any heavier teacher expansion:

```bash
python -u scripts/run_stage1_light_pipeline.py \
  --student_topk 30 \
  --teacher_topk 10 \
  --max_train_queries 2000 \
  --max_eval_queries 200
```

This pipeline will:

- measure baseline full-`1kA` candidate recall at `topk=30`
- build `ViCLIP` teacher supervision with visible `tqdm`
- run lightweight Stage 1 distillation
- auto-run `1kA 200-query` quick evaluation
- write the acceptance-gate decision json
