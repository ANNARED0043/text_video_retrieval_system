# Current Best

Active version: `stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1`

Metrics on locked `1kA q200`:

- `R@1 = 50.5`
- `R@5 = 64.5`
- `R@10 = 73.5`
- `MedR = 1.0`
- `MnR = 20.42`

Artifacts:

- Summary: `outputs/tables/analysis/stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json`
- Checkpoint: `outputs/tables/analysis/stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt`
- Memory: `outputs/tables/analysis/stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1_memory.json`
- Continual state: `outputs/tables/analysis/continual_layer_state.json`

Promotion rule:

- New candidates must first be evaluated as candidate summaries.
- Promote only if `R@1` improves by at least `0.5`, or if `R@1` ties and `MedR`/`MnR` improves.
- Do not promote a run that uses `1kA` ground truth as training signal.

Continual self-learning rule:

- Build feedback only from `safe_train` retrieval results and known `safe_train` gt.
- Store the gap between retrieved topK and gt in `self_feedback_memory_round*.jsonl`.
- Train a candidate from that feedback supervision plus replay/memory controls.
- Promote only after fixed-reference metrics do not regress and feedback diagnostics improve.
