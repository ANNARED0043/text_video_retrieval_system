# video_retrieval_system

## Locked Reference

The locked `MSRVTT 1kA 200-query` reference for this repository is:

- `R@1 = 48.5`
- `R@5 = 66.0`
- `R@10 = 73.5`

Reference artifact:

- [stage1_viclip_topk30_q800_quick200_conservative_v7_quick_eval.json](/e:/BISHE/video_retrieval_system/outputs/tables/analysis/stage1_viclip_topk30_q800_quick200_conservative_v7_quick_eval.json)

## Data Protocol

The repository now uses one leakage-safe split for training, one for validation, and one for final testing.

### Train Split: `safe_train`

- Purpose: model training
- Source: `MSRVTT Train 9K`
- Main split name: `safe_train`
- Files:
- Video list file: not stored separately; this split is defined implicitly as `Train 9K valid videos minus safe_dev videos`
- Query file (`.jsonl`): [msrvtt_train_9k_safe_train_queries.jsonl](/e:/BISHE/video_retrieval_system/data/annotations/msrvtt/msrvtt_train_9k_safe_train_queries.jsonl)
- Retrieval manifest (`.jsonl`): [msrvtt_fixed.jsonl](/e:/BISHE/video_retrieval_system/data/manifests/msrvtt_fixed.jsonl)

### Validation Split: `safe_dev`

- Purpose: model selection, quick gate, ablation
- Source: held-out split from `MSRVTT Train 9K`
- Main split name: `safe_dev`
- Files:
- Video list file (`.txt`): [safe_dev_video_list.txt](/e:/BISHE/video_retrieval_system/data/annotations/msrvtt/safe_dev_video_list.txt)
- Query file (`.jsonl`): [msrvtt_train_9k_safe_dev_queries.jsonl](/e:/BISHE/video_retrieval_system/data/annotations/msrvtt/msrvtt_train_9k_safe_dev_queries.jsonl)
- Retrieval manifest (`.jsonl`): [msrvtt_fixed_safe_dev.jsonl](/e:/BISHE/video_retrieval_system/data/manifests/msrvtt_fixed_safe_dev.jsonl)

### Test Split: `1kA`

- Purpose: locked final evaluation only
- Source: official `MSRVTT 1kA`
- Main split name: `1kA`
- Files:
- Video list file (`.txt`): [val_list_jsfusion.txt](/e:/BISHE/video_retrieval_system/data/annotations/msrvtt/val_list_jsfusion.txt)
- Query file (`.jsonl`): [msrvtt_1kA_test_queries.jsonl](/e:/BISHE/video_retrieval_system/data/annotations/msrvtt/msrvtt_1kA_test_queries.jsonl)
- Retrieval manifest (`.jsonl`): [msrvtt_fixed_1kA.jsonl](/e:/BISHE/video_retrieval_system/data/manifests/msrvtt_fixed_1kA.jsonl)

### Rule

- Train split = `safe_train`
- Validation split = `safe_dev`
- Test split = `1kA`

## Stage Plan

### Stage 1: System Optimization

- baseline retrieval
- query rewrite
- candidate rerank

### Stage 2: Representation Enhancement

- teacher-student distillation
- hard negative mining
- prototype-aware learning
- teacher soft labels

### Stage 3: Continual Learning and Memory

- prototype memory
- hard negative memory
- constraint memory
- acceptance-gated continual learning

## Working Rule

At the start of each new round, the active stage and its current responsibilities should be announced and written to [CURRENT_STAGE.md](/e:/BISHE/video_retrieval_system/CURRENT_STAGE.md).

## Auto Continual Learning

Run automatic strategy-controlled continual learning with quality feedback:

```powershell
python scripts\run_auto_continual_learning.py --strategy v35_plus --rounds 3 --success_target 0.80
```

Useful strategies:

- `v35_plus`: recommended when improving the current `R@1=50.5` run; starts from the v35 settings and only explores small perturbations.
- `hybrid_elite`: strongest default; tries multiple internal candidates per round and keeps only the best gated candidate.
- `discovla_precision`: stricter alignment/teacher filtering.
- `tokenbinder_margin`: stronger one-to-many/listwise candidate separation.
- `mama_replay`: broader replay-oriented memory learning.

By default, the auto learner evaluates on `safe_dev` for model selection and warm-starts from the current best checkpoint. Use `--eval_split 1kA` only for locked reporting, not for routine strategy tuning.

Each run writes:

- JSONL learning log: `outputs/feedback/auto_continual_learning_log.jsonl`
- Text feedback: `outputs/tables/analysis/auto_continual_learning/<run_id>/learning_feedback.md`
- Machine-readable feedback: `outputs/tables/analysis/auto_continual_learning/<run_id>/learning_feedback.json`

Rejected candidates are logged but do not replace the active best model.

Default teacher supervision uses `outputs/tables/analysis/viclip_teacher_supervision_stage2_safe_train_q500_cov100_t20_v1.jsonl`, which keeps the ground-truth video inside the saved teacher targets and is aligned with the default auto-learning setup.

## Error-Driven Agent Loop

For a stronger, paper-oriented continual-learning loop, use the error-driven curriculum command:

```powershell
python scripts\run_error_driven_agent_loop.py --rounds 1
```

This loop:

- starts from the current active best checkpoint
- first evaluates that checkpoint on the current `safe_dev` protocol as the round reference
- mines only high-value failed samples from `safe_train`
- defaults to the failure band `rank 2-30`
- rebuilds feedback teacher supervision
- warm-starts a new candidate
- promotes it only if the acceptance gate approves

Important:

- `1kA` is the locked reporting split
- `safe_dev` is the continual-learning selection split
- do not directly compare a `safe_dev` summary with the locked `1kA=50.5` result

If you want to inspect the selected failure band more explicitly:

```powershell
python scripts\build_self_feedback_supervision.py --manifest msrvtt_fixed.jsonl --queries msrvtt_train_9k_safe_train_queries.jsonl --max_queries 500 --search_topk 30 --teacher_topk 20 --checkpoint outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt --multiview_features outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz --multiview_weight 0.085 --alignment_teacher outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl --alignment_weight 0.085 --query_batch_size 4 --failed_only --min_gt_rank 1 --max_gt_rank 30 --out_memory outputs\tables\analysis\feedback_rank2_30_memory_q500.jsonl --out_teacher outputs\tables\analysis\feedback_rank2_30_teacher_q500.jsonl
```

## Front End

Launch the local interactive frontend with one command:

```powershell
python -m streamlit run front_end/app.py
```

The frontend provides `Home`, `Search Results`, `History`, `Learning Logs`, and `Ablations` pages.
