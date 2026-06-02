# Research Log

This log records the repository's key experiment steps, leakage-prevention decisions, and theory-backed implementation choices.

## Locked 1kA Reference

The locked `MSRVTT 1kA 200-query` reference used for planning is:

- `R@1 = 48.5`
- `R@5 = 66.0`
- `R@10 = 73.5`

Artifact:

- [stage1_viclip_topk30_q800_quick200_conservative_v7_quick_eval.json](/e:/BISHE/video_retrieval_system/outputs/tables/analysis/stage1_viclip_topk30_q800_quick200_conservative_v7_quick_eval.json)

## 2026-04-09 | Current Safety-First Plan

We are shifting the default quick-gate protocol away from the official `MSRVTT 1kA` test split and toward a deterministic dev split derived from `train_9k`. The immediate implementation goals are:

- create a video-disjoint safe `train/dev` split from `train_9k`
- switch Stage 1 quick evaluation defaults to the safe dev split
- keep `1kA test` for final locked evaluation only
- upgrade the text adapter to a more conservative gated residual form
- centralize experiment decisions and theory support in this root log

## Core References

- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: keep a strong video-text teacher while preserving a cheaper student retrieval path.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: efficient teacher-to-student distillation remains a strong path for lightweight retrieval improvement.
- MV-Adapter (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: parameter-efficient adaptation should account for language and alignment gaps, not only temporal vision transfer.
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: sentence-component-aware supervision is a promising low-cost route for fine-grained retrieval gains.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: benchmark protocol and validation quality matter because coarse metrics can hide weak semantic discrimination.
- DiscoVLA (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: lightweight retrieval adaptation benefits from explicitly modeling language-side and alignment-side discrepancies.

## 2026-04-09T14:30:08 | prepare_msrvtt_safe_split

Created leakage-safe train/dev split from train_9k with seed=20260409, dev_videos=500, train_videos=8500.

Decisions:
- Use only train_9k videos to derive the quick-gate dev split.
- Keep the official 1kA test split out of hyperparameter tuning and model selection.
- Make the split video-disjoint so the same video never appears in both train and dev queries.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_train_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_dev_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\safe_dev_video_list.txt

## 2026-04-09T14:32:12 | repository_hygiene::trash_move

Moved low-risk stale root files into trash to keep the project root focused on active assets and scripts.

Decisions:
- Only move low-risk root files that are clearly outside the main retrieval workflow.
- Do not move datasets, experiment artifacts, thesis materials, or active pipeline scripts.

Artifacts:
- e:\BISHE\video_retrieval_system\trash\.env.py
- e:\BISHE\video_retrieval_system\trash\test.py
- e:\BISHE\video_retrieval_system\trash\test_tdqm.py
- e:\BISHE\video_retrieval_system\trash\README.md

## 2026-04-09T14:38:01 | prepare_msrvtt_safe_split

Created leakage-safe train/dev split from train_9k with seed=20260409, dev_videos=500, train_videos=8500.

Decisions:
- Use only train_9k videos to derive the quick-gate dev split.
- Keep the official 1kA test split out of hyperparameter tuning and model selection.
- Make the split video-disjoint so the same video never appears in both train and dev queries.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_train_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_dev_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\safe_dev_video_list.txt

## 2026-04-09T14:38:13 | run_stage1_light_pipeline::stage1_viclip_topk30_safe_dev_quick200

Launch the leakage-safe Stage 1 pipeline with a safe train/dev split and a conservative adapter.

Decisions:
- Train queries default to msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval defaults to msrvtt_train_9k_safe_dev_queries.jsonl
- Adapter mode defaults to gated

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- outputs/tables/analysis/baseline_vith14_mean_topk200_safe_dev.json
- outputs/tables/analysis/viclip_teacher_supervision_stage1_topk30_safe_train.jsonl
- outputs/tables/analysis/stage1_viclip_topk30_safe_dev_quick200.json
- outputs/tables/analysis/stage1_viclip_topk30_safe_dev_gate.json

## 2026-04-09T14:38:14 | prepare_msrvtt_safe_split

Created leakage-safe train/dev split from train_9k with seed=20260409, dev_videos=500, train_videos=8500.

Decisions:
- Use only train_9k videos to derive the quick-gate dev split.
- Keep the official 1kA test split out of hyperparameter tuning and model selection.
- Make the split video-disjoint so the same video never appears in both train and dev queries.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_train_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_dev_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\safe_dev_video_list.txt

## 2026-04-09T14:40:58 | protocol_fix::safe_dev_manifest

Corrected the leakage-safe dev protocol to evaluate against a held-out safe-dev manifest instead of the full 10k manifest. The previous setup was not comparable to the 1kA protocol and artificially depressed the quick baseline.

Decisions:
- Safe dev now uses its own held-out manifest.
- Default dev size is raised to 1000 videos to better match the 1kA evaluation scale.
- Stage 1 pipeline now rebuilds a dedicated FAISS index for the safe-dev manifest before quick evaluation.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- e:\BISHE\video_retrieval_system\scripts\prepare_msrvtt_safe_split.py
- e:\BISHE\video_retrieval_system\scripts\run_stage1_light_pipeline.py

## 2026-04-09T14:41:05 | prepare_msrvtt_safe_split

Created leakage-safe train/dev split from train_9k with seed=20260409, dev_videos=1000, train_videos=8000.

Decisions:
- Use only train_9k videos to derive the quick-gate dev split.
- Keep the official 1kA test split out of hyperparameter tuning and model selection.
- Make the split video-disjoint so the same video never appears in both train and dev queries.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_train_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_dev_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\safe_dev_video_list.txt
- E:\BISHE\video_retrieval_system\data\manifests\msrvtt_fixed_safe_dev.jsonl

## 2026-04-09T14:42:40 | prepare_msrvtt_safe_split

Created leakage-safe train/dev split from train_9k with seed=20260409, dev_videos=1000, train_videos=6381.

Decisions:
- Use only train_9k videos to derive the quick-gate dev split.
- Keep the official 1kA test split out of hyperparameter tuning and model selection.
- Make the split video-disjoint so the same video never appears in both train and dev queries.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_train_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_dev_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\safe_dev_video_list.txt
- E:\BISHE\video_retrieval_system\data\manifests\msrvtt_fixed_safe_dev.jsonl

## 2026-04-09T14:45:56 | prepare_msrvtt_safe_split

Created leakage-safe train/dev split from train_9k with seed=20260409, dev_videos=1000, train_videos=6381.

Decisions:
- Use only train_9k videos to derive the quick-gate dev split.
- Keep the official 1kA test split out of hyperparameter tuning and model selection.
- Make the split video-disjoint so the same video never appears in both train and dev queries.

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_train_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\msrvtt_train_9k_safe_dev_queries.jsonl
- E:\BISHE\video_retrieval_system\data\annotations\msrvtt\safe_dev_video_list.txt
- E:\BISHE\video_retrieval_system\data\manifests\msrvtt_fixed_safe_dev.jsonl

## 2026-04-09T15:05:30 | stage_announcement::run_stage1_light_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Focus on baseline retrieval, query rewrite, and candidate rerank before heavier representation learning.

## 2026-04-09T15:05:34 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T15:09:18 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-05-01 | Stage 3 高质量样本扩展诊断

目的：
- 将“扩大训练 query 数”与“扩大有效高质量学习样本数”区分开，避免把 q500/q800/q1500 的规模变化误认为真实有效监督变化。
- 新增实验因素：有效高质量样本数。后续实验命名必须写清楚候选 query 数、最终有效样本数、teacher/alignment/multiview 状态和评测协议。

过程：
- 新增 `scripts/diagnose_high_quality_learning_pool.py`，用于在正式训练前统计 teacher supervision 在给定 gate 下可筛出的有效样本数量和质量。
- 扩展该脚本，使其能够导出高质量 query 子集与 teacher 子集；后续可先扩大候选范围，再只围绕高质量样本训练。
- 升级 `teacher_pairwise_weight` 的实际作用：除原有 teacher list 内排序约束外，新增 GT-vs-hard-negative 的强排序约束，使 teacher 更明确地教 student 区分正确视频与相似错误候选。
- 新增 `--query_aware_fusion`，对 action、relation、person_attribute 等组件更复杂的 query 提高 alignment/multiview 权重，避免固定融合权重对所有 query 一刀切。
- 新增 `--component_view_weight`，将 query 中的 action/object/scene/relation 组件文本单独编码，并与 early/middle/late multiview 视频向量进行显式局部匹配。该项用于解决 multiview 只作为补充分数、没有学习“哪个局部证据对应哪个 query component”的问题。
- 细化视频侧 multiview token：`scripts/build_multiview_video_features.py` 新增 `--view_segments`，默认保留 3 视角，建议后续 q1500 使用 6 个 temporal view tokens，使 component-to-view alignment 有更细的视频侧证据。
- 使用当前 q500 teacher supervision 诊断：500 个候选 query 中有 222 条通过筛选，未达到目标 500 条。
- 使用旧 q800 teacher supervision 诊断：该文件未强制保留 GT，出现大量 `gt_missing_in_teacher`，不适合作为高质量筛选学习来源。

结果：
- 当前最好 q200 方法不应继续命名为模糊的 v3.5，而应在论文和实验表中写成 `stage3_align_multiview_q500_effective222_eval1kAq200`。
- 下一步应构建更大范围且强制保留 GT 的 teacher supervision，再通过 gate 筛选出约 500 条高质量样本，而不是直接复用旧 q800 或简单扩大 q。

结论：
- 当前瓶颈之一不是 teacher/multiview 思路无效，而是高质量可学习样本数量不足。
- 新实验主线为：扩大 safe_train 候选范围 -> 强制 GT 覆盖 -> teacher 质量筛选 -> 只用高质量样本训练 -> component-to-view alignment -> 对比 q500 effective222 与 highquality500 的 locked 1kA 结果。

Artifacts:
- `scripts/diagnose_high_quality_learning_pool.py`
- `docs/stage3_high_quality_learning_experiment_plan.md`
- `outputs/tables/analysis/diagnose_highquality_pool_q500_rank12_target500_v1.json`
- `outputs/tables/analysis/diagnose_highquality_pool_q500_rank12_target500_v2.json`
- `outputs/tables/analysis/teacher_subset_highquality222_from_q500_rank12_v1.jsonl`
- `outputs/tables/analysis/queries_subset_highquality222_from_q500_rank12_v1.jsonl`
- `outputs/tables/analysis/diagnose_highquality_pool_q800_rank12_target500_v1.json`

## 2026-04-09T15:09:18 | stage_announcement::run_rerank_eval

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run selective rewrite plus candidate rerank inside the system-optimization stage.

## 2026-04-09T15:21:16 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-04-09T15:24:40 | run_llm_pipeline::rewrite_selective_hybrid

Evaluated Stage 1 system optimization mode=rewrite_selective_hybrid on msrvtt_train_9k_safe_dev_queries.jsonl with R@1=39.0, R@5=62.0, R@10=71.0.

Decisions:
- Manifest: msrvtt_fixed_safe_dev.jsonl
- Queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Hybrid baseline alpha: 0.75

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75_summary.json

## 2026-04-09T15:40:07 | stage_announcement::run_rerank_eval

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run selective rewrite plus candidate rerank inside the system-optimization stage.

## 2026-04-09T15:40:39 | stage_announcement::run_rerank_eval

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run selective rewrite plus candidate rerank inside the system-optimization stage.

## 2026-04-09T21:22:23 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-04-09T21:25:49 | run_llm_pipeline::rewrite_selective_hybrid

Evaluated Stage 1 system optimization mode=rewrite_selective_hybrid on msrvtt_1kA_test_queries.jsonl with R@1=48.0, R@5=67.5, R@10=73.5.

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Hybrid baseline alpha: 0.75

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75_summary.json

## 2026-04-09T21:52:44 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-04-09T21:53:05 | run_llm_pipeline::rewrite_selective_hybrid

Evaluated Stage 1 system optimization mode=rewrite_selective_hybrid on msrvtt_1kA_test_queries.jsonl with R@1=48.0, R@5=67.5, R@10=73.5.

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Hybrid baseline alpha: 0.75

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.2_ba0.75_summary.json

## 2026-04-09T21:54:03 | stage_announcement::run_rerank_eval

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run selective rewrite plus candidate rerank inside the system-optimization stage.

## 2026-04-09T22:04:47 | run_rerank_eval::rewrite_selective

Evaluated rewrite+rereank mode on msrvtt_1kA_test_queries.jsonl with selective rerank=False. Metrics: R@1=48.0, R@5=65.0, R@10=72.5.

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Rerank only if rewritten: False

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\week7_rewrite_selective_mean_topk200_rerank5_alpha0.8_thr0.2.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\week7_rewrite_selective_mean_topk200_rerank5_alpha0.8_thr0.2_summary.json

## 2026-04-09T22:28:22 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-04-09T22:28:48 | run_llm_pipeline::rewrite_selective_hybrid

Evaluated Stage 1 system optimization mode=rewrite_selective_hybrid on msrvtt_1kA_test_queries.jsonl with R@1=48.0, R@5=67.0, R@10=72.5.

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Hybrid baseline alpha: 0.8

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.25_ba0.8.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.25_ba0.8_summary.json

## 2026-04-09T22:29:17 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-04-09T22:29:48 | run_llm_pipeline::rewrite_selective_hybrid

Evaluated Stage 1 system optimization mode=rewrite_selective_hybrid on msrvtt_1kA_test_queries.jsonl with R@1=47.5, R@5=65.0, R@10=72.5.

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Hybrid baseline alpha: 0.85

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.3_ba0.85.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_hybrid_mean_topk200_thr0.3_ba0.85_summary.json

## 2026-04-09T22:31:05 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-04-09T22:31:36 | run_llm_pipeline::rewrite_selective_riskaware

Evaluated Stage 1 system optimization mode=rewrite_selective_riskaware on msrvtt_1kA_test_queries.jsonl with R@1=46.5, R@5=67.0, R@10=74.5.

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Hybrid baseline alpha: 0.75

Theory Support:
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: Validation should stress subtle semantics instead of relying only on coarse benchmark wins.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_riskaware_mean_topk200_thr0.25_la0.68_sa0.55.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\final_rewrite_selective_riskaware_mean_topk200_thr0.25_la0.68_sa0.55_summary.json

## 2026-04-09 | 阶段一总结（中文）

### 实验目的

本轮阶段一实验的目标是验证“系统型优化”是否还能在当前 `ViT-H-14 / laion2b_s32b_b79k` 基线之上继续带来稳定收益。我们重点比较了三类方案：

- 基线检索
- 基于基线的选择性 query rewrite
- 基于 rewrite 的 candidate rerank

本轮统一以 `MSRVTT 1kA` 的 `200 query` 结果作为对比口径。

### 实验过程

1. 先重新确认当前批次 baseline：
   `R@1 = 47.5 / R@5 = 65.0 / R@10 = 72.0`
2. 运行两组 `rewrite_selective_hybrid` 配置：
   - `ambiguity_threshold = 0.25, hybrid_baseline_alpha = 0.80`
   - `ambiguity_threshold = 0.30, hybrid_baseline_alpha = 0.85`
3. 运行一组 `rewrite_selective_riskaware` 配置：
   - `ambiguity_threshold = 0.25`
4. 对已有的 `rewrite + rerank(top5)` 结果一并纳入判断。

### 实验结果

基线：

- `R@1 = 47.5`
- `R@5 = 65.0`
- `R@10 = 72.0`

Hybrid 配置 1：

- `R@1 = 48.0`
- `R@5 = 67.0`
- `R@10 = 72.5`
- `rewrite_rate = 0.525`

Hybrid 配置 2：

- `R@1 = 47.5`
- `R@5 = 65.0`
- `R@10 = 72.5`
- `rewrite_rate = 0.185`

Risk-aware 配置：

- `R@1 = 46.5`
- `R@5 = 67.0`
- `R@10 = 74.5`
- `rewrite_rate = 0.525`

补充参考：已有 `rewrite + rerank(top5)` 结果为：

- `R@1 = 48.0`
- `R@5 = 65.0`
- `R@10 = 72.5`

### 可视化

- 对比图：
  [stage1_q200_rewrite_comparison.png](/e:/BISHE/video_retrieval_system/outputs/figures/stage1_q200_rewrite_comparison.png)

### 结论

本轮阶段一实验说明：

- `rewrite` 确实能带来一定帮助，但提升幅度已经比较有限
- 当前最好的系统型优化配置是 `rewrite_selective_hybrid (thr=0.25, ba=0.80)`
- 这一配置相对同批次 baseline 仅实现：
  `R@1 +0.5 / R@5 +2.0 / R@10 +0.5`
- `rerank(top5)` 当前没有表现出稳定额外收益
- `risk-aware rewrite` 虽然改善了 `R@10`，但会明显伤害 `R@1`

因此，阶段一可以视为已经完成主要探索：系统型优化路径存在小幅收益，但已经接近上限，不适合作为后续主提分方向。

## 2026-04-09 | 阶段二启动计划（中文）

### 当前阶段

当前正式进入：

- `Stage 2: Representation Enhancement`

当前负责内容：

- teacher-student distillation
- hard negative mining
- prototype-aware learning
- teacher soft labels

### 阶段二要做什么

阶段二的核心目标是不再依赖 query 侧补丁式优化，而是把 teacher 的排序与语义信号迁移到 student 表征中。当前最适合本项目的执行路径是：

1. 使用现有 `ViT-H` baseline 检索得到候选集
2. 使用 `ViCLIP teacher` 对候选集重新打分，构建 teacher supervision
3. 在 `top-k` 候选内做轻量 student distillation
4. 配合 hard negatives、prototype-aware learning 和 teacher soft labels
5. 先在 `safe_dev` 上做 quick gate，再决定是否推到 `1kA`

### 阶段二建议的最小可跑方案

- teacher：`ViCLIP`
- student：当前已实现的保守 adapter
- student candidate set：`topk = 30`
- teacher topk：`10`
- 先跑保守参数：
  - `hard_negatives = 4 或 6`
  - `residual_scale = 0.04 或 0.05`
  - `similarity_teacher_weight = 0.05 或 0.06`

### 预计时长

如果只跑“最小 Stage 2”一轮，按当前仓库与本地约束，预计时间如下：

- 生成或复用 safe split：约 `1~3 分钟`
- 构建 teacher supervision：约 `20~60 分钟`
- 跑一轮轻量 student distillation：约 `15~40 分钟`
- quick eval 与 gate：约 `5~15 分钟`

合计：

- 单轮最小 Stage 2：约 `40~120 分钟`

如果做 2~3 组保守参数对比：

- 预计总时长：约 `1.5~3 小时`

### 阶段二目标

阶段二的目标不是立刻追求最终最高分，而是先做到：

- 在 `safe_dev` 上稳定超过阶段一最佳系统型配置
- 在 `1kA q200` 上至少稳定高于当前同批次 baseline `47.5 / 65.0 / 72.0`
- 如果 quick gate 稳定通过，再继续推进到更完整的 Stage 2 / Stage 3

## 2026-04-09T22:44:10 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T22:44:58 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T22:50:35 | run_stage_experiment::stage2_bootstrap_safe_dev_q800_eval200_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: bootstrap_vith_retrieval

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_bootstrap_safe_dev_q800_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_bootstrap_safe_dev_q800_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_bootstrap_safe_dev_q800_eval200_v1_quick_eval.json


## 2026-04-09 | ???????????

?????
- ????????? `safe_train / safe_dev` ?????? Stage 2 ????????????? ViT-H-14 ???????????
- ?????????????????????????????????????????

?????
- ????`msrvtt_train_9k_safe_train_queries.jsonl`
- ????`msrvtt_train_9k_safe_dev_queries.jsonl`
- ???????`msrvtt_fixed.jsonl`
- ???????`msrvtt_fixed_safe_dev.jsonl`
- ?????`ViT-H-14 / laion2b_s32b_b79k`
- ???????`bootstrap_vith_retrieval`?????? ViCLIP HuggingFace ???? `configuration_viclip.py`?`viclip.py`?`model.safetensors` ? tokenizer ????????????? ViCLIP teacher?
- ???????800
- ???????????362
- ??????200
- ?????`teacher soft labels + hard negative mining + prototype-aware learning + memory-based sampling`

?????
- baseline?R@1 = 39.0?R@5 = 60.5?R@10 = 71.0?MnR = 44.665
- adapter?R@1 = 41.0?R@5 = 62.5?R@10 = 71.5?MnR = 41.045
- ?????fused88 / fused90 / fused92????? adapter??????????????????????????????????

?????
- ?? Stage 2 ????????????????????????
- ???????????????????????? Stage 1 ? rewrite/rerank ?????????????????????
- ?????? bootstrap teacher????????????????????????Stage 2 ??????????????

???
- ????Stage 2 ????????????????? Stage 1 rerank?
- ????????????????????????????????? query rewrite?
- ??????????????????????????? `q1500~q2000`?????? `safe_dev` ??????????

?????
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  ?????????????????????????
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  ???????????????????????????????
- DiscoVLA (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  ????????????????????????

?????
- `outputs/tables/analysis/stage2_bootstrap_safe_dev_q800_eval200_v1.json`
- `outputs/tables/analysis/stage2_bootstrap_safe_dev_q800_eval200_v1.pt`
- `outputs/tables/analysis/stage2_bootstrap_safe_dev_q800_eval200_v1_quick_eval.json`
- `outputs/figures/stage2_safe_dev_q800_eval200_v1.png`


## 2026-04-09T22:51:44 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T23:00:57 | run_stage_experiment::stage2_bootstrap_safe_dev_q1500_eval200_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=43.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: bootstrap_vith_retrieval

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_bootstrap_safe_dev_q1500_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_bootstrap_safe_dev_q1500_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_bootstrap_safe_dev_q1500_eval200_v1_quick_eval.json


## 2026-04-09 | ????????????

?????
- ? Stage 2 ??????????????????? `q800` ??? `q1500` ?????????????????

?????
- ???`safe_train / safe_dev`
- ???????1500
- ????????711
- ??????200
- ?????`bootstrap_vith_retrieval`
- ?????`hard negative mining + teacher soft labels + prototype-aware learning + memory sampling`

?????
- baseline?R@1 = 39.0?R@5 = 60.5?R@10 = 71.0?MnR = 44.665
- Stage2 q1500 adapter?R@1 = 43.0?R@5 = 63.5?R@10 = 72.5?MnR = 37.575
- ?? baseline?R@1 +4.0?R@5 +3.0?R@10 +1.5?MnR -7.090

?????
- ????????Stage 2 ?????? `q800` ????????????????
- `fused88 / fused90 / fused92` ????? adapter??????????????????????????????
- ???? quick gate ????? Stage 1 ??????????? Stage 2 ????????

?????
- ?? Stage 2 ??????????
- ?????????? safe_dev ?????????????? `q2000`???????? rank ????????????

?????
- `outputs/tables/analysis/stage2_bootstrap_safe_dev_q1500_eval200_v1.json`
- `outputs/tables/analysis/stage2_bootstrap_safe_dev_q1500_eval200_v1.pt`
- `outputs/figures/stage2_safe_dev_scaling_q800_q1500.png`


## 2026-04-09T23:28:15 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T23:36:52 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T23:39:32 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T23:40:34 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-09T23:41:33 | run_stage_experiment::stage2_viclip_safe_dev_q200_eval200_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=39.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q200_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q200_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q200_eval200_v1_quick_eval.json

## 2026-04-10T01:55:21 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T01:56:08 | run_stage_experiment::stage2_viclip_safe_dev_q200_eval200_gpu_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=39.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q200_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q200_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q200_eval200_gpu_v1_quick_eval.json

## 2026-04-10T02:03:54 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T02:04:34 | run_stage_experiment::stage2_viclip_1kA_q200_eval200_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_q200_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_q200_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_q200_eval200_v1_quick_eval.json

## 2026-04-10T14:34:51 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T14:35:46 | run_stage_experiment::stage2_viclip_safe_dev_q500_eval200_gpu_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_safe_dev_q500_eval200_gpu_v1_quick_eval.json

## 2026-04-10T14:39:35 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T14:40:24 | run_stage_experiment::stage2_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 1 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10 | 阶段二路线确认（中文）

当前结论：
- `ViCLIP teacher + q500` 已经在 `1kA q200` 上带来稳定增益，可作为当前 Stage 2 的有效基线。
- 当前不急于直接跳到 Stage 3，而是先把 Stage 2 内部的几个关键模块拆开做完整，再回头继续扩大蒸馏规模。

当前基线结果：
- baseline（1kA q200）：R@1 = 47.5，R@5 = 65.0，R@10 = 72.0
- Stage 2 adapter（ViCLIP teacher, train q500, eval 1kA q200）：R@1 = 48.5，R@5 = 66.5，R@10 = 73.5

阶段二后续执行顺序：
- Stage 2A：固定 `ViCLIP teacher + q500` 为当前表征增强基线，并保留已有 teacher 文件与实验结果
- Stage 2B：在 `q500` 基线上强化 hard negative mining
- Stage 2C：在 `q500` 基线上强化 prototype-aware learning 与 teacher soft labels
- Stage 2D：在保留前面结果的前提下，从 `q500` 继续续蒸馏到更大规模（如 `q800`）
- Stage 2E：重新汇总蒸馏增强与其他表征增强模块，得到综合结果

为什么这样安排：
- 当前已经证明蒸馏是有效的，因此没有必要只盯着蒸馏规模单线推进
- Stage 2 的其他部分同样会受到 teacher supervision 的影响，因此完全可以先固定一版强 teacher 基线，再做其他模块增强
- 后续更大规模的蒸馏结果，也可以反过来继续提升 hard negatives、prototype-aware learning 和 soft labels 的质量

当前决策：
- 保留 `q500` 结果作为 Stage 2 当前默认基线
- 后续所有 Stage 2 小实验，优先与这版基线比较
- 开发中继续使用无泄露训练协议；关键节点再回 `1kA q200` 做统一对比

关键产物：
- `outputs/tables/analysis/viclip_teacher_supervision_stage2_safe_train_q500_gpu_v1.jsonl`
- `outputs/tables/analysis/stage2_viclip_1kA_train500_eval200_gpu_v1.json`
- `outputs/tables/analysis/stage2_viclip_1kA_train500_eval200_gpu_v1.pt`

## 2026-04-10T14:55:18 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.


## 2026-04-10 | 阶段二B：hard negative mining 增强（中文）

实验目的：
- 在已经验证有效的 `ViCLIP teacher + q500` 基线之上，优先强化 Stage 2 的 hard negative mining，观察更强负样本是否能继续推高 R@1 / R@5 / R@10。

本次实现：
- 将原来的 `top-k similarity negatives` 升级为 `teacher_hybrid` 模式。
- 新模式优先引入 teacher supervision 中已经暴露出的 hard negatives / listwise targets / similarity targets。
- 在 teacher negatives 之外，再补充不同 rank bucket 的相似负样本，避免负样本过于单一，只集中在最靠前的一小段。
- 当前 bucket 策略为：近邻强负样本 + 中段半难负样本 + 远段多样化负样本。

设计理由：
- 仅使用最相似 top-k 负样本，容易造成训练信号过窄，模型更像是在反复区分“几个最像的样本”，而不是学习更稳的排序边界。
- teacher supervision 已经提供了更细的相关性信息，因此 hard negative 应该优先吸收 teacher 暴露出的困难错误样本。
- 适度加入 mid / far bucket 负样本，有助于提升泛化而不是只对局部邻域过拟合。

代码变更：
- `src/learning/text_adapter.py`
  - 新增 teacher-aware hard negative 选择逻辑
  - 新增 `teacher_hybrid` 负样本模式
- `scripts/run_stage_experiment.py`
  - 新增 `--hard_negative_mode {topk,teacher_hybrid}` 参数
  - 默认切换为 `teacher_hybrid`

当前状态：
- Stage 2B 代码已完成并通过轻量验证
- 下一步直接在 `q500 teacher` 基线上跑对比实验，观察 `teacher_hybrid` 是否优于原始 `topk`


## 2026-04-10T15:10:13 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T15:11:02 | run_stage_experiment::stage2b_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2b_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2b_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2b_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10T15:27:21 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10 | ???C?prototype-aware learning ? teacher soft labels ??????

?????
- ??? `ViCLIP teacher + q500` ????????? Stage 2 ? prototype-aware learning ? teacher soft labels?

?????
- ? semantic memory ? teacher supervision ?????? query token ????? `the / and / with / about / talking` ??????
- ? teacher soft labels ?? `teacher_temperature`??? teacher ????????????
- ?? `prototype_teacher_weight`?? teacher supervision ?? `prototype_terms` ?????????

?????
- Stage 2C ?????????? `q500 teacher` ?????????

## 2026-04-10T15:28:27 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T15:29:16 | run_stage_experiment::stage2c_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2c_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2c_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2c_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10 | Stage 2D：动态负样本过滤与更宽 soft-label 蒸馏

目的：
- 修正 Stage 2B / 2C 中 hard negatives 与 soft labels 提升有限的问题。
- 在不改动总体训练框架的前提下，让 teacher supervision 更有效地传递到 adapter。

过程：
- 为 hard negative mining 增加疑似假负样本过滤，减少 false negatives 。
- 将蒸馏候选集从“正样本 + 少量 hard negatives”扩展为“正样本 + hard negatives + teacher targets”。
- 将相似度蒸馏改为 teacher-only 的 masked soft-label 分布蒸馏。
- 将 listwise teacher supervision 改为基于 teacher 排名权重的 listwise loss。
- 新增参数：`--distill_candidate_topk` 与 `--false_negative_margin`。

结果：
- 当前已完成代码落地与脚本验证。
- 下一步将固定 `q500 teacher -> 1kA q200 eval` 做统一对比。

理论支持：
- ADAM (ACL Findings 2024)
  Reason: teacher soft labels 需要保留更宽的暗知识分布。
- Hard Negatives or False Negatives (CIKM 2022)
  Reason: 强负样本中可能混入假负样本，需要过滤。
- Text Is MASS (CVPR 2024)
  Reason: 文本表示和匹配分布存在不确定性。
- MV-Adapter (CVPR 2024)
  Reason: 参数高效适配需要更合理的监督信号。

Artifacts:
- src/learning/text_adapter.py
- scripts/run_stage_experiment.py

## 2026-04-10T15:43:50 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T15:44:45 | run_stage_experiment::stage2d_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Distill candidate topk: 30
- False negative margin: 0.02

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2d_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2d_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2d_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10 | 论文方法设计稿草案整理

目的：
- 将当前项目从“工程优化堆叠”收束为可写论文的方法主线。
- 明确后续算法创新点，避免继续做分散式补丁优化。

结论：
- 当前最值得作为论文重点的方法方向为“不确定性感知原型蒸馏”。
- 该方向将 query uncertainty、teacher soft labels、structured prototypes、memory-gated update 统一到一个框架内。
- 对应方法草案已整理到 `docs/PAPER_METHOD_DRAFT.md`。

建议：
- 先完成 `q800 teacher supervision`。
- 再优先实现 uncertainty-aware temperature 与 structured prototype distillation。
- 后续在验证有效后，再接入 memory-gated update。

Artifacts:
- docs/PAPER_METHOD_DRAFT.md

## 2026-04-10T17:02:18 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T17:03:22 | run_stage_experiment::stage2_viclip_1kA_train800_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=47.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_train800_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_train800_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2_viclip_1kA_train800_eval200_gpu_v1_quick_eval.json

## 2026-04-10 | q800 蒸馏无额外优势，主线转向不确定性感知蒸馏

目的：
- 记录 `q800 teacher` 在统一 `1kA q200` 评测口径下未能超过当前最优 `q500 teacher` 的结论。
- 明确后续主线不再继续扩蒸馏规模，而是转向改进蒸馏机制本身。

结果：
- 当前最优仍为 `q500 teacher` 对应的 `adapter = 48.5 / 66.5 / 73.5`。
- `q800 teacher` 结果未超过 `q500 teacher`，说明瓶颈不再主要来自 teacher 数量，而在于 teacher 信号如何被 student 吸收。

决定：
- 停止将“继续扩大蒸馏规模”作为当前优先路线。
- 下一步进入“不确定性感知蒸馏”的最小可验证版本。
- 首先实现 query-aware teacher temperature，并保留现有 `q500/q800 teacher` 文件可直接复用。

## 2026-04-10 | 不确定性感知蒸馏第一版落地

目的：
- 将论文方法草案中的第一步真正转化为可运行代码。
- 在不增加大量训练时间的前提下，让 teacher soft labels 的强度随 query 不确定性动态变化。

过程：
- 在 `src/learning/text_adapter.py` 中新增 teacher uncertainty 估计逻辑。
- 若 teacher supervision 中已有 `uncertainty_score`，则直接复用。
- 若没有，则从 teacher top targets 的 top1-top2 gap 与分布熵中在线计算 uncertainty。
- 将固定 `teacher_temperature` 改为 query-aware 的动态温度：
  - 明确 query 使用更低温度
  - 含混 query 使用更高温度
- 在 `scripts/run_stage_experiment.py` 中新增参数：
  - `--uncertainty_aware_temperature`
  - `--teacher_temperature_min`
  - `--teacher_temperature_max`
- 在 `scripts/build_viclip_teacher_supervision.py` 中为后续新生成的 teacher supervision 自动写入：
  - `teacher_top1_top2_gap`
  - `teacher_entropy`
  - `uncertainty_score`

说明：
- 该版本对已有 `q800 teacher` 文件兼容，无需重新蒸馏即可直接训练。
- 下一步应固定 `1kA q200` 口径，验证 uncertainty-aware temperature 是否超过当前 `48.5 / 66.5 / 73.5`。

Artifacts:
- src/learning/text_adapter.py
- scripts/run_stage_experiment.py
- scripts/build_viclip_teacher_supervision.py

## 2026-04-10T17:10:25 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T17:20:29 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T17:21:20 | run_stage_experiment::stage2e_uncertainty_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2e_uncertainty_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2e_uncertainty_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2e_uncertainty_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10T17:24:33 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10 | ???????????????????

???
- ?? uncertainty-aware temperature ???????????????????
- ?????????????????????? structured prototype distillation?

???
- uncertainty-aware temperature ? `q500 teacher -> 1kA q200` ??????????? `48.5 / 66.5 / 73.5`?
- ??????????????????????

???
- ?? uncertainty-aware temperature ???????????????????
- ??????? structured prototype distillation?

## 2026-04-10 | ????????????

???
- ? prototype ? token overlap/bonus ?????????????????????
- ??????????????????? action/object/scene ?? prototype ???

???
- ? `src/llm/semantic_memory.py` ??? `extract_structured_prototypes`?? query ????
  - action prototypes
  - object prototypes
  - scene prototypes
- ? `src/learning/teacher_supervision.py` ?? teacher supervision ?? `structured_prototypes` ???
- ? `scripts/build_viclip_teacher_supervision.py` ???????? teacher ??????? prototypes?
- ? `scripts/run_stage_experiment.py` ? bootstrap teacher ?????????? prototypes???????
- ? `src/learning/text_adapter.py` ??? `structured_prototype_weight` ???? prototype ?????

???
- ?????? `q500 teacher` ???????????? `structured_prototypes` ?????????
- ????????? `q500 teacher -> 1kA q200` ????????

Artifacts:
- src/llm/semantic_memory.py
- src/learning/teacher_supervision.py
- src/learning/text_adapter.py
- scripts/build_viclip_teacher_supervision.py
- scripts/run_stage_experiment.py

## 2026-04-10T17:33:57 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T17:34:52 | run_stage_experiment::stage2f_structured_proto_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2f_structured_proto_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2f_structured_proto_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2f_structured_proto_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10 | ??????????

???
- ??????? `q500 teacher` ? `q800 teacher`??????????? prototype ????????
- ??????????????????????????????????

???
- ??????????????????????????????
- ?????????
  - teacher coverage ??
  - teacher ??????
  - student ????????????
  - ???????????????????
- ??????????? `docs/BOTTLENECK_ANALYSIS.md`?

???
- ??????????????????? + ???? teacher supervision + ??? prototype learning??
- ???????????????

Artifacts:
- docs/BOTTLENECK_ANALYSIS.md

## 2026-04-10 | ??????????????

???
- ???????????????????? segment ????????????????
- ????????????????????????

???
- ? `src/learning/text_adapter.py` ????????? `mean pooling` ????
  - `video_matrix`?mean pooled video features
  - `video_max_matrix`?max pooled video features
- ? `TextResidualAdapter` ??? query-conditioned video gate?
  - ?? query ???? mean/max ???????????
- ????????????????????????
- ? `scripts/run_stage_experiment.py` ??????
  - `--video_aggregation_weight`

???
- ???????????????????? segment feature?
- ??????????????? 3 ??????????

Artifacts:
- src/learning/text_adapter.py
- scripts/run_stage_experiment.py
- docs/BOTTLENECK_ANALYSIS.md

## 2026-04-10T21:47:03 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T21:52:17 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T21:53:14 | run_stage_experiment::stage2g_videoagg_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2g_videoagg_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2g_videoagg_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2g_videoagg_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10T21:57:47 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T22:06:19 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T22:08:02 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-10T22:08:56 | run_stage_experiment::stage2h_reliable_teacher_videoagg_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 5
- Teacher min margin: 0.01
- Teacher max uncertainty: 0.95
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2h_reliable_teacher_videoagg_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2h_reliable_teacher_videoagg_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2h_reliable_teacher_videoagg_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-10 | ?? teacher coverage ???????

???
- ????????????????teacher supervision ? ground-truth ??????
- ???????? teacher ????????

???
- ? `scripts/build_viclip_teacher_supervision.py` ??? teacher coverage ???
- ?? `--force_keep_gt_in_teacher` ???
- ? ground-truth ??? teacher ????????? topk ????????? ground-truth ????? teacher targets?
- ? teacher metadata ????
  - `gt_rank_full`
  - `gt_rank_saved`
  - `gt_forced_into_teacher`
- ????????? coverage ???
  - `gt_in_full_targets`
  - `gt_in_saved_targets`
  - `teacher_top1_is_gt`

???
- ?????????? loss??????? teacher supervision ???????
- ?????????? teacher ??????????

Artifacts:
- scripts/build_viclip_teacher_supervision.py

## 2026-04-11T00:00:56 | stage_announcement::run_stage_experiment

Entered Stage 2: Representation Enhancement.

Decisions:
- Current responsibilities: teacher-student distillation, hard negative mining, prototype-aware learning, teacher soft labels
- Focus on teacher-student distillation, hard negatives, prototype-aware learning, and teacher soft labels.

## 2026-04-11T00:01:54 | run_stage_experiment::stage2i_highcov_teacher_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 10
- Teacher min margin: 0.005
- Teacher max uncertainty: 0.98
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2i_highcov_teacher_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2i_highcov_teacher_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage2i_highcov_teacher_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-11 | ???? Stage 2 ??????? Stage 3

???
- ?????? Stage 2 ???????? Stage 2 ?????????
- ???? Stage 3?prototype memory / hard negative memory / constraint memory / acceptance-gated continual learning?

???
- ???? Stage 2 ???? `q500 teacher -> 48.5 / 66.5 / 73.5`?
- ???????? memory ????????

## 2026-04-11 | Stage 3 ????acceptance-gated memory ??????

???
- ? memory ?????????????????????????????????
- ????????????????gt ??????????? memory?

???
- ? `scripts/run_stage_experiment.py` ??? Stage 3 ???
  - `--stage_key stage3`
  - `--acceptance_gated_memory`
  - `--acceptance_max_teacher_rank`
  - `--acceptance_max_uncertainty`
  - `--acceptance_min_overlap`
  - `--memory_refresh_topk`
- ?? acceptance score?
  - ?? teacher gt rank?teacher uncertainty?prototype overlap ??????????
- ?? stage3 memory snapshot?
  - `prototype_memory`
  - `hard_negative_memory`
  - `constraint_memory`
  - `accepted_qids`
- ? accepted qids ??????????????????? Stage 3 ???
- ??????????? memory json?

???
- Stage 3 ??????????-??-gt ???????? memory?????????????
- ?????????????????????????

Artifacts:
- scripts/run_stage_experiment.py

## 2026-04-11T00:20:00 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24 | 自学习 agent 控制接口检查

目的：确认当前检索 agent 是否能够通过“学习策略 + 学习轮次/数量”进行自动迭代，并且在没有正向增益时拒绝本轮学习，避免污染当前最优模型。

结果：`scripts/run_auto_continual_learning.py` 已支持 `--strategy` 和 `--rounds` 控制学习策略与轮次；每轮会训练多个 candidate，选择质量分最高者进入 promotion gate。未通过质量门控或 active-best 晋升门控的候选会写入日志，但不会覆盖当前 v3.5 最优版本。

本次调整：将自动学习反馈中的 80% 成功率目标改为显式参数 `--success_target`，便于后续实验按目标 success rate 记录学习质量。后续推荐使用 `hybrid_elite` 或 `v35_plus`，并以 1kA q200 作为锁定报告集，safe_train/safe_dev 作为学习与模型选择数据，继续防止数据泄露。

补充检查：自动学习脚本原默认 `teacher_supervision` 指向的 stage1 文件当前不存在，已改为当前工作区存在的 `outputs/tables/analysis/viclip_teacher_supervision_stage2_safe_train_q500_gpu_v1.jsonl`，避免一条命令真实运行时因教师监督文件缺失而失败。

## 2026-04-24 | 自学习链路机制修正

目的：修正当前 continual learning 中“看起来在学习，实际上没有真正接着当前最佳模型继续学”的机制问题，并排查 memory 未生效的根因。

发现：

- 自动学习脚本此前只把 `current_best` 用作晋升比较基线，没有把当前最佳 checkpoint 传入训练初始化，因此每轮更接近“重新训练新 adapter”，不是真正的持续学习。
- 先前默认 teacher 文件 `viclip_teacher_supervision_stage2_safe_train_q500_gpu_v1.jsonl` 中，GT 并不总在保存的 teacher targets 内，导致 acceptance-gated memory 可能整轮 `accepted=0`。
- baseline / adapter 评测此前混入了 `semantic_memory` 与 `alignment_teacher` 的检索时 bonus，不利于判断 student 表征是否真的学到了东西。

本次修正：

- `run_auto_continual_learning.py` 现在会自动从 `current_best` summary 中解析 checkpoint，并把它传给 `run_stage_experiment.py` 作为 warm-start 初始化。
- 自动学习默认 teacher 改为 `outputs/tables/analysis/viclip_teacher_supervision_stage2_safe_train_q500_cov100_t20_v1.jsonl`，该文件保存了 GT 目标，更适合 acceptance-gated memory。
- 自动学习默认改为 `safe_dev` 做模型选择，避免继续把 `1kA` 当日常调参门控集使用。
- `run_stage_experiment.py` 现已将“纯学习效果评测”和“带 memory/alignment bonus 的系统评测”拆开：`methods` 记录纯 baseline/adapter，`augmented_methods` 记录加 bonus 后的系统效果。

意义：这样后续看到的 `methods.adapter` 更接近“模型真正学会了多少”，而不是“检索时外部 bonus 帮了多少”；同时 continual learning 终于具备了“从当前最佳模型继续优化”的基本前提。

## 2026-04-24 | front_end 可视化页面搭建

目的：为当前文本检索视频系统补齐可交互网页，支持随机 benchmark query、手动 query、Top5 视频播放、历史记录、学习日志、消融分析与用户反馈入口。

实现：

- 在根目录新建 `front_end` 文件夹，并创建 `front_end/app.py` 与 `front_end/README.md`。
- 页面结构采用单入口多页面导航：`Home`、`Search Results`、`History`、`Learning Logs`、`Ablations`。
- `Home` 支持随机抽取测试 query、按 QID 选择 benchmark query、手动输入自然语言 query，并支持多选 `baseline / rewrite / rerank` 检索方式与搜索深度参数。
- `Search Results` 会显示 Top5 视频并直接播放；benchmark query 会显示 GT rank，手动 query 不显示 GT rank，但支持保存用户反馈并写入学习队列。
- `History` 保留最近 10 次搜索并支持跳回对应结果页。
- `Learning Logs` 汇总 auto continual learning 日志、learning diary 与用户反馈队列。
- `Ablations` 汇总已有 summary、失败诊断、candidate recall 与可视化分析说明。

说明：当前仓库 `requirements.txt` 已包含 `streamlit`，但本次执行环境中未实际安装该包，因此前端代码已完成，启动级静态验证受限于本地环境依赖。

## 2026-04-11T00:20:55 | run_stage_experiment::stage3_memory_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=47.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 10
- Teacher min margin: 0.005
- Teacher max uncertainty: 0.98
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-11T00:34:33 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-11T00:35:19 | run_stage_experiment::stage3_memory_filter_viclip_1kA_train500_eval200_gpu_v2

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 10
- Teacher min margin: 0.005
- Teacher max uncertainty: 0.98
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_filter_viclip_1kA_train500_eval200_gpu_v2.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_filter_viclip_1kA_train500_eval200_gpu_v2.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_filter_viclip_1kA_train500_eval200_gpu_v2_quick_eval.json

## 2026-04-11T00:50:00 | stage3_memory_augmented_scoring

目的：
- 将 Stage 3 从“仅基于 acceptance gate 过滤训练样本”升级为“让 memory 直接参与训练与评测打分”。

问题诊断：
- 旧版 Stage 3 已经启用了 memory filter，但主要效果是缩小训练集，尚未把历史高置信文本-视频-gt 对齐经验直接注入相似度分数。
- 因此提升有限，更像降噪筛样本，而不是利用 memory 做知识增强。

本次改动：
- 在 stage3 memory snapshot 中新增 `prototype_video_memory`，记录高置信结构化原型到 gt 视频的加权关联。
- 在训练阶段，对候选视频分数加入 memory bonus。
- 在评测阶段，对全库视频分数加入同样的 memory bonus，使 memory 真正参与检索排序。

理论依据：
- 当前瓶颈不在于继续增加 teacher 数量，而在于如何把稳定历史经验转化为可复用的检索先验。
- 该设计更接近“记忆增强检索”而非“样本过滤”，更符合 Stage 3 的持续学习目标。

## 2026-04-11T01:10:00 | stage3_memory_augscore_result_analysis

结果结论：
- Stage 3 的 memory-augmented scoring 在当前设置下对 MnR 有轻微改善，但未带来 R@1、R@5、R@10 的新增益。
- 这说明 memory 目前更像对中后段排序的温和修正，而不是能把更多正确视频推进到 top1/top5 的强头部增强机制。

分析判断：
- 当前最优主结果仍然是 Stage 2 的 q500 teacher 版本：48.5 / 66.5 / 73.5。
- Stage 3 已经真正参与训练和评分，但其主要收益体现在平均排名改善，而非头部召回突破。
- 根本原因仍在于 teacher 排序质量不足、student 容量较轻、memory 对头部样本的判别力不足。

系统机制说明：
- 当前系统不是“每次用户搜索之后，根据新一次搜索结果和 gt 自动在线更新”的真实在线持续学习系统。
- 当前实现更准确地说是“离线批量式持续学习”：
  1. 使用已有训练查询、gt、teacher supervision 构建 memory。
  2. 用 acceptance gate 筛选高置信样本。
  3. 训练 adapter，并在评测时使用 memory 参与打分。
  4. 评测阶段本身不会根据本次检索结果再即时回写和更新模型。
- 因此它属于“基于历史高置信文本-视频-gt 经验的阶段式持续学习”，还不是严格意义上的逐次在线 continual learning。

## 2026-04-11T01:30:00 | bc_alignment_upgrade

目的：
- 在不做 teacher 全库重排的前提下，推进 B/C 两条主线：
  1. teacher-first 的候选与排序蒸馏；
  2. 跨模态文本-视频对齐增强。

本次改动：
- 候选构造新增 `teacher_first_candidates`，优先使用 teacher 给出的排序候选，而不是先依赖 student 挖出的 hard negatives。
- 新增 `teacher_pairwise_weight`，对 teacher 排序前列样本加入 pairwise 顺序约束。
- 新增 `cross_modal_video_weight`，让视频表示在打分时受 query 条件化影响，避免系统只在文本侧微调。

设计依据：
- 参考 TeachCLIP、MV-Adapter、DiscoVLA 等工作，当前瓶颈不只是文本表征，还包括跨模态对齐和视频侧适配。
- 当前 top30 candidate recall 约 83.5%~83.8%，可先在候选池内做更强的 teacher-first alignment 学习，再决定是否需要更大召回池。

## 2026-04-11T01:45:00 | stage3_memory_quality_monitor

目的：
- 为 Stage 3 的多轮持续学习补充 memory 质量监控，避免只看 accepted 数量。

本次补充：
- 在 stage3 memory stats 中新增：
  - accepted_gt_rank_mean
  - accepted_top1_is_gt
  - accepted_top1_is_gt_rate
  - accepted_uncertainty_mean
  - accepted_prototype_overlap_mean
- 在 summary 中新增：
  - accepted_before_rank_filter
  - accepted_after_rank_filter
  - train_rows_used

意义：
- 后续多轮实验不仅要看 Recall，还要同时判断 memory 的数量、排序质量和置信度是否在变好。

## 2026-04-23T14:30:00 | multiframe_alignment_teacher_v1

目标：
- 在 RTX 4060 + i9-14900 + 16GB 内存的 3 小时预算内，先落地轻量多帧特征、人物粗属性、动作顺序和 alignment teacher 证据。

本次实现：
- 新增 `scripts/build_multiframe_alignment_teacher.py`。
- 对每个视频按时间顺序抽取稀疏多帧。
- 使用现有 OpenCLIP/ViT-H-14 做零样本 prompt probing，生成：
  - age_group 粗粒度伪标签；
  - person_type 粗粒度伪标签；
  - scene 伪标签；
  - top actions；
  - action_sequence。

注意事项：
- 当前实现是轻量版 pseudo alignment teacher，不是专门的人脸年龄/性别检测器，也不是全量动作识别模型。
- 输出应作为软监督和 alignment evidence 使用，不能当作人口属性真值。
- 该版本优点是无需新增重依赖，能在当前工程和 3 小时预算内先跑通多帧语义增强。

## 2026-04-23T15:05:00 | multiframe_alignment_teacher_integration

目的：
- 将多帧 alignment teacher 从离线产物接入训练和评测链路。

本次实现：
- `run_stage_experiment.py` 新增 `--alignment_teacher` 和 `--alignment_teacher_weight`。
- `text_adapter.py` 在训练候选 logits 中加入 query 与多帧 teacher 标签的语义对齐 bonus。
- 评测阶段同样加入 alignment teacher bonus，使多帧属性、场景、动作顺序证据直接影响检索排序。

使用方式：
- 推荐先使用 `outputs/tables/analysis/multiframe_alignment_teacher_1kA_f6_v1.jsonl`。
- 该 teacher 覆盖 1kA 视频，适合固定 `1kA q200` 做对比。

## 2026-04-23T15:20:00 | alignment_teacher_v2_sequence_and_memory_gate

结果背景：
- `stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1` 达到 R@1=49.0，超过此前 Stage 2 最优 R@1=48.5。

本次增强：
- 在 alignment bonus 中加入 action sequence 顺序匹配分数。
- 在 Stage 3 acceptance gate 中加入 alignment_overlap，可让 memory 更偏向多帧语义一致的样本。
- Summary 中会继续记录 memory 质量，并新增 accepted_alignment_overlap_mean。

目的：
- 将多帧属性、动作顺序和 alignment teacher 从“检索加分项”进一步用于 memory 质量控制。

## 2026-04-23T15:35:00 | alignment_teacher_f6_gate_result

结果：
- `stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2` 达到 adapter R@1=49.5。
- 相比原始 baseline R@1=47.5，提升 +2.0。
- 相比此前 Stage 2 最优 R@1=48.5，提升 +1.0。

诊断：
- 多帧 alignment teacher 对 1kA 评测排序已经产生正向作用。
- 但 memory_stats 中 accepted_alignment_overlap_mean=0.0，说明 alignment teacher 当前主要覆盖 1kA 评测视频，尚未覆盖 safe_train 中用于训练和 memory gate 的 gt 视频。

下一步：
- 需要为训练侧 q500 涉及的 gt 视频和 teacher target 视频生成多帧 alignment teacher。
- 让 alignment evidence 同时进入训练、memory acceptance 和评测，而不是只在 1kA 评测侧发挥作用。

## 2026-04-23T16:05:00 | alignment_teacher_v3_1_v3_2_ready

完成情况：
- v3.1 已完成：训练侧 q500 gt 视频多帧 alignment teacher 已生成。
- v3.2 已完成：训练侧 q500 teacher targets / hard negatives 多帧 alignment teacher 已生成。
- 已合并训练侧与 1kA 评测侧 alignment teacher，生成统一文件：
  `outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v1.jsonl`。

覆盖情况：
- 1kA alignment teacher：1000 个视频。
- safe_train q500 gt alignment teacher：100 个唯一 gt 视频。
- safe_train q500 teacher targets alignment teacher：4302 个视频。
- 合并后唯一视频数：4873。

下一步：
- 使用合并后的 alignment teacher 重新跑固定 1kA q200 验证。
- 重点观察 R@1 是否超过 49.5，以及 accepted_alignment_overlap_mean 是否从 0.0 变为有效值。

## 2026-04-23T16:20:00 | alignment_teacher_v3_3_fine_grained_prompts

结果背景：
- `stage3_alignment_teacher_train_targets_1kA_f6_v3` 维持 R@1=49.5。
- accepted_alignment_overlap_mean 从 0.0 提升到 0.088987，说明训练侧 alignment teacher 已经进入 memory gate，但细粒度对齐命中率仍偏低。

本次增强：
- 扩展年龄/人物 prompt：baby、child、teenager、adult、elderly、boy、girl、group、couple 等。
- 扩展动作 prompt：cutting、stirring、mixing、pouring、shooting、reading、speaking、exercising、demonstrating 等。
- 扩展场景 prompt：court、news_studio、bedroom、garage、snow、market、classroom、concert 等。
- 同步扩展 query 侧 action/object/scene 词表，使 query prototype 与 alignment teacher 更容易匹配。

目的：
- 提升多帧属性检测、动作序列建模和 alignment teacher 的细粒度覆盖。
- 进一步提高 accepted_alignment_overlap_mean，并观察是否能带来 R@1 新增益。

## 2026-04-23T17:20:00 | alignment_layer_v3_5_multiview_video_vectors

目的：
- 将视频侧从单一 video-level 向量扩展为 early / middle / late 三个多视角向量。

本次实现：
- 新增 `scripts/build_multiview_video_features.py`，可为 1kA、safe_train q500 gt、safe_train q500 teacher targets 定向生成多视角 CLIP 特征。
- `text_adapter.py` 支持读取 multiview `.npz`，并在训练和评测时计算 query 与多视角视频向量的最大匹配分。
- `run_stage_experiment.py` 新增 `--multiview_features` 与 `--multiview_weight`。

设计原因：
- v3.3 已证明多帧 alignment teacher 有效，但当前视频视觉表示仍主要是单向量。
- 多视角向量可以显式建模视频早/中/晚阶段语义，为动作顺序和细粒度对齐提供更强视频侧信息。

## 2026-04-23T19:10:00 | alignment_layer_v3_5_multiview_ready

完成情况：
- 1kA 多视角视频向量已生成：1000 个视频，形状为 (1000, 3, 1024)。
- safe_train q500 teacher targets 多视角视频向量已生成：4302 个视频，形状为 (4302, 3, 1024)。
- 已合并为统一文件：
  `outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz`。
- 合并后覆盖 4873 个唯一视频，每个视频包含 early / middle / late 三个视角向量。

三类 discrepancy 对应策略：
- Vision discrepancy：用 early/middle/late 多视角向量替代单一视频向量，增强视频侧时序和局部语义。
- Language discrepancy：扩展 query 侧 action/object/scene 词表，提升文本细粒度语义解析。
- Alignment discrepancy：用多帧 alignment teacher 与多视角向量共同参与训练和评测打分。

下一步：
- 固定 1kA q200 运行 v3.5 评测，观察 R@1 是否超过 50.0，以及 R@5/R@10 是否恢复。

## 2026-04-11T00:41:02 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-11T00:41:48 | run_stage_experiment::stage3_memory_augscore_viclip_1kA_train500_eval200_gpu_v3

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 10
- Teacher min margin: 0.005
- Teacher max uncertainty: 0.98
- Memory augmented weight: 0.12
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_augscore_viclip_1kA_train500_eval200_gpu_v3.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_augscore_viclip_1kA_train500_eval200_gpu_v3.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_memory_augscore_viclip_1kA_train500_eval200_gpu_v3_quick_eval.json

## 2026-04-11T01:04:09 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-11T01:04:57 | run_stage_experiment::stage3_bc_teacherfirst_xmodal_viclip_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 10
- Teacher min margin: 0.005
- Teacher max uncertainty: 0.98
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_viclip_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_viclip_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_viclip_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-11T01:20:25 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-11T01:21:18 | run_stage_experiment::stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2_quick_eval.json

## 2026-04-23T14:00:14 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T14:01:08 | run_stage_experiment::stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=48.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_bc_teacherfirst_xmodal_relaxed_viclip_1kA_train500_eval200_gpu_v2_quick_eval.json

## 2026-04-23T14:51:49 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T14:52:47 | run_stage_experiment::stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=49.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_1kA_f6_v1.jsonl
- Alignment teacher weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_f6_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-23T14:59:28 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T15:00:23 | run_stage_experiment::stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_1kA_f6_v1.jsonl
- Alignment teacher weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_f6_gate_1kA_train500_eval200_gpu_v2_quick_eval.json

## 2026-04-23T16:04:04 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T16:05:03 | run_stage_experiment::stage3_alignment_teacher_train_targets_1kA_f6_v3

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v1.jsonl
- Alignment teacher weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_train_targets_1kA_f6_v3.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_train_targets_1kA_f6_v3.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_train_targets_1kA_f6_v3_quick_eval.json

## 2026-04-23T17:49:38 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T17:50:43 | run_stage_experiment::stage3_alignment_teacher_train_targets_1kA_f6_v33

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_train_targets_1kA_f6_v33.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_train_targets_1kA_f6_v33.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_teacher_train_targets_1kA_f6_v33_quick_eval.json

## 2026-04-23T19:05:06 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T19:06:09 | run_stage_experiment::stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1_quick_eval.json

## 2026-04-23T19:16:08 | implementation::teacher_layer_alignment_distillation

已实现 Teacher Layer v1：从单纯 listwise distillation 升级为 alignment distillation，支持 query 的 action/object/scene/relation 拆解、候选视频伪 dense caption、多视角向量校准、局部 component alignment 监督。

Decisions:
- 新增 teacher 校准脚本，输出带 component_alignment metadata 的 teacher supervision。
- 训练脚本新增 component_alignment_weight，使 student 同时学习总排序分布和局部对齐分布。
- structured prototypes 增加 relation 维度，服务关系/人物交互类 query。
- 保持 1kA 只作为验证/对比，不把测试集 gt 写入训练 teacher。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- scripts/calibrate_teacher_with_alignment.py
- src/learning/text_adapter.py
- scripts/run_stage_experiment.py
- src/llm/semantic_memory.py

## 2026-04-23 | teacher_layer::alignment_distillation_q200_result

本轮 Teacher Layer 优化已完成代码接入与 q200 验证。结论是：alignment distillation 的数据链路已经打通，但当前版本没有超过 v3.5 多视角 alignment 的最优结果；因此暂时保留 v3.5 作为当前最好版本，Teacher Layer v1 作为后续继续精调的可复用模块。

Decisions:
- 已生成 alignment-calibrated teacher：outputs\tables\analysis\viclip_teacher_supervision_q500_alignment_calibrated_v1.jsonl。
- 已生成 base-preserve component teacher：outputs\tables\analysis\viclip_teacher_supervision_q500_alignment_basepreserve_v1.jsonl。
- alignment-calibrated teacher 覆盖 500 个 query 和 10000 个 target，alignment/multiview 覆盖率均为 100%，校准后 teacher top1 命中 gt 为 122/500。
- q200 评测中，v3.5 当前最好 adapter 为 R@1=50.5、R@5=64.5、R@10=73.5。
- Teacher Layer v1 三个验证版本最高 adapter 为 R@1=50.0，未超过 v3.5，说明局部对齐监督可以使用，但当前权重和伪标签粒度还不足以带来稳定增益。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: teacher-student distillation 需要保护强 teacher 的全局排序质量，避免弱局部信号扰动主排序。
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: 多视角视频侧信号仍是当前最有效增益来源。
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: 后续应继续细化 vision/language/alignment 三类 discrepancy，而不是简单增加 loss 权重。

Artifacts:
- outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_v1.json
- outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_w004_v1.json
- outputs\tables\analysis\stage3_teacher_layer_basepreserve_component_1kA_train500_eval200_w004_v1.json

## 2026-04-23T19:17:52 | teacher_layer::alignment_calibrated_v1

Teacher Layer v1 已将 listwise distillation 升级为 alignment distillation：每个 query 拆为 action/object/scene/relation，并为候选视频写入局部对齐分数与伪 dense caption。

Decisions:
- Base teacher supervision: outputs\tables\analysis\viclip_teacher_supervision_stage2_safe_train_q500_cov100_t20_v1.jsonl
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Calibration weights: base=0.55, alignment=0.25, multiview=0.2
- 输出 teacher supervision 中保留 component_alignment，后续 student 通过 component_alignment_weight 学局部对齐。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\viclip_teacher_supervision_q500_alignment_calibrated_v1.jsonl

## 2026-04-23T19:18:12 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T19:21:23 | run_stage_experiment::stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.12
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_v1_quick_eval.json

## 2026-04-23T19:21:44 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T19:24:50 | run_stage_experiment::stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_w004_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.04
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_w004_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_w004_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_alignment_calibrated_1kA_train500_eval200_w004_v1_quick_eval.json

## 2026-04-23T19:25:27 | teacher_layer::alignment_calibrated_v1

Teacher Layer v1 已将 listwise distillation 升级为 alignment distillation：每个 query 拆为 action/object/scene/relation，并为候选视频写入局部对齐分数与伪 dense caption。

Decisions:
- Base teacher supervision: outputs\tables\analysis\viclip_teacher_supervision_stage2_safe_train_q500_cov100_t20_v1.jsonl
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Calibration weights: base=1.0, alignment=0.0, multiview=0.0
- 输出 teacher supervision 中保留 component_alignment，后续 student 通过 component_alignment_weight 学局部对齐。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning (CVPRW 2024): https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html
  Reason: Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\viclip_teacher_supervision_q500_alignment_basepreserve_v1.jsonl

## 2026-04-23T19:25:44 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T19:28:45 | run_stage_experiment::stage3_teacher_layer_basepreserve_component_1kA_train500_eval200_w004_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.04
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_basepreserve_component_1kA_train500_eval200_w004_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_basepreserve_component_1kA_train500_eval200_w004_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_teacher_layer_basepreserve_component_1kA_train500_eval200_w004_v1_quick_eval.json

## 2026-04-23T19:40:35 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T20:07:51 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T20:09:03 | run_stage_experiment::continual_ab_no_memory_1kA_train500_eval200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_no_memory_1kA_train500_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_no_memory_1kA_train500_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_no_memory_1kA_train500_eval200_v1_quick_eval.json

## 2026-04-23T20:13:43 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T20:14:42 | run_stage_experiment::continual_ab_current_memory_1kA_train500_eval200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_current_memory_1kA_train500_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_current_memory_1kA_train500_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_current_memory_1kA_train500_eval200_v1_quick_eval.json

## 2026-04-23T20:15:02 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T20:16:00 | run_stage_experiment::continual_ab_strict_memory_1kA_train500_eval200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 8
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.99
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 8/0.99/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_strict_memory_1kA_train500_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_strict_memory_1kA_train500_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_strict_memory_1kA_train500_eval200_v1_quick_eval.json

## 2026-04-23T20:17:02 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state_no_memory.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state_no_memory.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T20:17:39 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state_current_memory.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state_current_memory.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T20:18:03 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state_strict_memory.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_layer_state_strict_memory.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T20:21:41 | continual_layer::effect_diagnosis

已完成 Continual Layer 多轮效果诊断：不只检查晋升，还检查 memory 是否真实带来正向学习信号。

Decisions:
- memory 有正向证据：current_memory 比 no_memory 的 R@1 高 1.00。
- 注意：memory 提升 R@1 的同时降低了 R@5，说明它更偏 top1 校准，泛化召回仍需改进。
- strict_memory 变差：gate 过严会减少有效训练样本，不建议收紧到当前设置。
- relaxed_memory 缺失：第四轮没有生成 summary，无法判断放宽 gate 的效果。
- 本组实验最优 candidate 是 current_memory。
- current_memory 没有低于 fixed reference，可作为候选继续观察。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_effect_diagnosis_v1.json

## 2026-04-23T20:23:39 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T20:24:45 | run_stage_experiment::continual_ab_relaxed_memory_1kA_train500_eval200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=50.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 15
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.998
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 15/0.998/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_relaxed_memory_1kA_train500_eval200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_relaxed_memory_1kA_train500_eval200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_ab_relaxed_memory_1kA_train500_eval200_v1_quick_eval.json

## 2026-04-23T20:27:34 | continual_layer::effect_diagnosis

已完成 Continual Layer 多轮效果诊断：不只检查晋升，还检查 memory 是否真实带来正向学习信号。

Decisions:
- memory 有正向证据：current_memory 比 no_memory 的 R@1 高 1.00。
- 注意：memory 提升 R@1 的同时降低了 R@5，说明它更偏 top1 校准，泛化召回仍需改进。
- strict_memory 变差：gate 过严会减少有效训练样本，不建议收紧到当前设置。
- relaxed_memory 与 current_memory 持平：需要用 feedback set 再判断是否值得放宽。
- 本组实验最优 candidate 是 relaxed_memory。
- current_memory 没有低于 fixed reference，可作为候选继续观察。
- relaxed_memory 没有低于 fixed reference，可作为候选继续观察。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_effect_diagnosis_v2.json

## 2026-04-23T20:34:17 | continual_layer::self_learning_agent_design

已新增自学习反馈层脚本：agent 可以从 safe_train 检索结果与正确 gt 的差距中构建 feedback memory，再转成下一轮训练监督。

Decisions:
- 反馈来源限定为 safe_train 检索结果与 safe_train gt，避免 1kA 泄露。
- 每轮先构建 self_feedback_memory，再训练 candidate adapter。
- 候选结果必须通过 fixed reference 与 feedback 诊断，才允许晋升为 current best。
- 当前机制是离线安全自学习闭环，可继续扩展到用户点击或人工反馈。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- scripts/build_self_feedback_supervision.py
- CURRENT_BEST.md

## 2026-04-23T21:43:37 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:45:08 | run_stage_experiment::auto_hybrid_elite_round01_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c01_summary_quick_eval.json

## 2026-04-23T21:45:19 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:46:44 | run_stage_experiment::auto_hybrid_elite_round01_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c02_summary_quick_eval.json

## 2026-04-23T21:46:53 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:48:20 | run_stage_experiment::auto_hybrid_elite_round01_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_c03_summary_quick_eval.json

## 2026-04-23T21:48:21 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round01_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T21:48:28 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:49:57 | run_stage_experiment::auto_hybrid_elite_round02_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c01_summary_quick_eval.json

## 2026-04-23T21:50:05 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:51:35 | run_stage_experiment::auto_hybrid_elite_round02_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c02_summary_quick_eval.json

## 2026-04-23T21:51:43 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:53:12 | run_stage_experiment::auto_hybrid_elite_round02_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_c03_summary_quick_eval.json

## 2026-04-23T21:53:13 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round02_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T21:53:20 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:54:48 | run_stage_experiment::auto_hybrid_elite_round03_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round03_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round03_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round03_c01_summary_quick_eval.json

## 2026-04-23T21:54:56 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T21:56:25 | run_stage_experiment::auto_hybrid_elite_round03_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round03_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round03_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_214328_hybrid_elite_safe_dev\round03_c02_summary_quick_eval.json

## 2026-04-23T22:02:20 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:03:23 | run_stage_experiment::auto_v35_plus_round01_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c01_summary_quick_eval.json

## 2026-04-23T22:03:32 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:04:37 | run_stage_experiment::auto_v35_plus_round01_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.07200000000000001
- Teacher first candidates: True
- Teacher pairwise weight: 0.075
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08800000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c02_summary_quick_eval.json

## 2026-04-23T22:04:45 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:05:50 | run_stage_experiment::auto_v35_plus_round01_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9979849999999999
- Memory augmented weight: 0.1
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9979849999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c03_summary_quick_eval.json

## 2026-04-23T22:05:58 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:07:03 | run_stage_experiment::auto_v35_plus_round01_c04

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.066
- Cross-modal video weight: 0.08000000000000002
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.07200000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.096
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c04_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c04_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_c04_summary_quick_eval.json

## 2026-04-23T22:07:05 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round01_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-23T22:07:12 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:08:18 | run_stage_experiment::auto_v35_plus_round02_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c01_summary_quick_eval.json

## 2026-04-23T22:08:26 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:09:32 | run_stage_experiment::auto_v35_plus_round02_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.07200000000000001
- Teacher first candidates: True
- Teacher pairwise weight: 0.075
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08800000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c02_summary_quick_eval.json

## 2026-04-23T22:09:41 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-23T22:10:47 | run_stage_experiment::auto_v35_plus_round02_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9979849999999999
- Memory augmented weight: 0.1
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9979849999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260423_220215_v35_plus_1kA\round02_c03_summary_quick_eval.json

## 2026-04-23T22:10:55 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:19:35 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:21:10 | run_stage_experiment::auto_hybrid_elite_round01_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c01_summary_quick_eval.json

## 2026-04-24T00:21:20 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:22:50 | run_stage_experiment::auto_hybrid_elite_round01_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c02_summary_quick_eval.json

## 2026-04-24T00:22:58 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:24:29 | run_stage_experiment::auto_hybrid_elite_round01_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_c03_summary_quick_eval.json

## 2026-04-24T00:24:31 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round01_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T00:24:38 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:26:10 | run_stage_experiment::auto_hybrid_elite_round02_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c01_summary_quick_eval.json

## 2026-04-24T00:26:18 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:27:53 | run_stage_experiment::auto_hybrid_elite_round02_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c02_summary_quick_eval.json

## 2026-04-24T00:28:01 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:29:35 | run_stage_experiment::auto_hybrid_elite_round02_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_c03_summary_quick_eval.json

## 2026-04-24T00:29:36 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round02_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T00:29:44 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:31:19 | run_stage_experiment::auto_hybrid_elite_round03_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c01_summary_quick_eval.json

## 2026-04-24T00:31:27 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:33:01 | run_stage_experiment::auto_hybrid_elite_round03_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=50.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c02_summary_quick_eval.json

## 2026-04-24T00:33:09 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:34:44 | run_stage_experiment::auto_hybrid_elite_round03_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_c03_summary_quick_eval.json

## 2026-04-24T00:34:45 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\round03_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T00:34:45 | continual_layer::effect_diagnosis

已完成 Continual Layer 多轮效果诊断：不只检查晋升，还检查 memory 是否真实带来正向学习信号。

Decisions:
- relaxed_memory 缺失：第四轮没有生成 summary，无法判断放宽 gate 的效果。
- 本组实验最优 candidate 是 round02。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\diagnosis.json

## 2026-04-24T00:34:45 | auto_continual_learning::feedback

Completed auto continual learning run 20260424_001926_hybrid_elite_1kA with strategy=hybrid_elite; quality_success_rate=0.0, promotion_success_rate=0.0.

Decisions:
- Strategy description: DiscoVLA-style discrepancy reduction + TokenBinder-style one-to-many candidate comparison + conservative memory replay.
- Eval split: 1kA
- Rounds: 3
- Quality target 80% met: False
- Rejected candidates are logged and do not overwrite the active best model.

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.
- Video Understanding: Through A Temporal Lens (arXiv 2026): https://researchtrend.ai/papers/2602.00683
  Reason: Noise-robust contrastive learning and LVLM-augmented annotations motivate cautious replay and teacher filtering.
- Make Your Training Flexible: Towards Deployment-Efficient Video Models (ICCV 2025): https://github.com/OpenGVLab/FluxViT
  Reason: Dynamic token and view selection motivates stronger multiview feature selection under fixed compute.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\learning_feedback.md
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\learning_feedback.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_001926_hybrid_elite_1kA\diagnosis.json
- E:\BISHE\video_retrieval_system\outputs\feedback\auto_continual_learning_log.jsonl

## 2026-04-24T00:47:35 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:48:39 | run_stage_experiment::auto_hybrid_elite_round01_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c01_summary_quick_eval.json

## 2026-04-24T00:48:46 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:49:50 | run_stage_experiment::auto_hybrid_elite_round01_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c02_summary_quick_eval.json

## 2026-04-24T00:49:58 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:51:04 | run_stage_experiment::auto_hybrid_elite_round01_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_c03_summary_quick_eval.json

## 2026-04-24T00:51:06 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round01_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T00:51:13 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:52:18 | run_stage_experiment::auto_hybrid_elite_round02_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c01_summary_quick_eval.json

## 2026-04-24T00:52:26 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:53:32 | run_stage_experiment::auto_hybrid_elite_round02_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c02_summary_quick_eval.json

## 2026-04-24T00:53:40 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:54:48 | run_stage_experiment::auto_hybrid_elite_round02_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_c03_summary_quick_eval.json

## 2026-04-24T00:54:50 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round02_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T00:54:56 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:56:02 | run_stage_experiment::auto_hybrid_elite_round03_c01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c01_summary_quick_eval.json

## 2026-04-24T00:56:10 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:57:18 | run_stage_experiment::auto_hybrid_elite_round03_c02

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.0675
- Teacher first candidates: True
- Teacher pairwise weight: 0.08125
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.09350000000000001
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.07475
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c02_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c02_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c02_summary_quick_eval.json

## 2026-04-24T00:57:28 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T00:58:39 | run_stage_experiment::auto_hybrid_elite_round03_c03

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=41.0, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.00255
- Teacher max uncertainty: 0.9949759999999999
- Memory augmented weight: 0.09375
- Teacher first candidates: True
- Teacher pairwise weight: 0.065
- Cross-modal video weight: 0.1
- Alignment teacher: outputs/tables/analysis/multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs/tables/analysis/multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.9949759999999999/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c03_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c03_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_c03_summary_quick_eval.json

## 2026-04-24T00:58:40 | continual_layer::state_update

Continual Layer 已启动：当前以 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过 v3.5 的 Teacher Layer 结果覆盖当前最高版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\round03_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T00:58:40 | continual_layer::effect_diagnosis

已完成 Continual Layer 多轮效果诊断：不只检查晋升，还检查 memory 是否真实带来正向学习信号。

Decisions:
- 本组自动学习最优 candidate 是 round03。
- 本组自动学习没有候选超过当前最佳 R@1。
- 本组候选在更宽召回上也没有形成稳定优势。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\diagnosis.json

## 2026-04-24T00:58:40 | auto_continual_learning::feedback

Completed auto continual learning run 20260424_004729_hybrid_elite_safe_dev with strategy=hybrid_elite; quality_success_rate=0.0, promotion_success_rate=0.0.

Decisions:
- Strategy description: DiscoVLA-style discrepancy reduction + TokenBinder-style one-to-many candidate comparison + conservative memory replay.
- Eval split: safe_dev
- Rounds: 3
- Quality target 80% met: False
- Rejected candidates are logged and do not overwrite the active best model.

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.
- Video Understanding: Through A Temporal Lens (arXiv 2026): https://researchtrend.ai/papers/2602.00683
  Reason: Noise-robust contrastive learning and LVLM-augmented annotations motivate cautious replay and teacher filtering.
- Make Your Training Flexible: Towards Deployment-Efficient Video Models (ICCV 2025): https://github.com/OpenGVLab/FluxViT
  Reason: Dynamic token and view selection motivates stronger multiview feature selection under fixed compute.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\learning_feedback.md
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\learning_feedback.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\auto_continual_learning\20260424_004729_hybrid_elite_safe_dev\diagnosis.json
- E:\BISHE\video_retrieval_system\outputs\feedback\auto_continual_learning_log.jsonl

## 2026-04-24T01:08:38 | continual_layer::failure_diagnosis

已完成当前检索模型失败样本诊断，统计不同 rank bucket 和 query 语义类型下的错误分布。

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Checkpoint: outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt
- Top failure buckets: {'top11_30': 31, 'top1': 99, 'top2_5': 33, 'gt_outside_top30': 22, 'top6_10': 15}
- Top failure tags: {'object': 72, 'relation': 67, 'person_attribute': 53, 'action': 43, 'scene': 14}

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.
- blim_iccv2025

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\failure_diagnosis_v35_1kA_q200.json

## 2026-04-24T01:15:35 | continual_layer::failure_diagnosis

已完成当前检索模型失败样本诊断，统计不同 rank bucket 和 query 语义类型下的错误分布。

Decisions:
- Manifest: msrvtt_fixed_1kA.jsonl
- Queries: msrvtt_1kA_test_queries.jsonl
- Checkpoint: outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt
- Top failure buckets: {'top11_30': 31, 'top1': 99, 'top2_5': 33, 'gt_outside_top30': 22, 'top6_10': 15}
- Top failure tags: {'object': 72, 'relation': 67, 'person_attribute': 53, 'action': 43, 'scene': 14}

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.
- blim_iccv2025

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\failure_diagnosis_v35_1kA_q200.json

## 2026-04-24T01:16:30 | continual_layer::self_feedback_supervision

已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，把正样本和 hard negatives 写入 feedback memory 与下一轮 teacher supervision。

Decisions:
- Queries: 500
- Top1 is gt rate: 0.284
- Mean gt rank: 228.17
- Memory output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\self_feedback_failedonly_memory_q500_v1.jsonl
- Teacher supervision output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\self_feedback_failedonly_teacher_q500_v1.jsonl
- 仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\self_feedback_failedonly_memory_q500_v1.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\self_feedback_failedonly_teacher_q500_v1.jsonl

## 2026-04-24T10:30:00 | continual_layer::error_driven_loop_design

已把当前自学习闭环收束为“错误驱动课程学习”方案：先从当前最优模型中抽取 `rank 2-30` 的高价值失败样本，再构建 feedback teacher，warm-start 训练 candidate，并通过 promotion gate 决定是否晋升。

Decisions:
- 新增 `run_error_driven_agent_loop.py`，用一条命令串起 feedback teacher、candidate 训练和 gate 审核。
- `build_self_feedback_supervision.py` 新增 `max_gt_rank`，支持只学习 near-failure 样本。
- 修正了 continual 状态更新和 feedback supervision 的中文日志，避免后续论文整理时出现乱码。
- 在根目录新增《论文方法设计稿草案》，开始收束论文的算法贡献与系统贡献。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: 需要同时处理 vision / language / alignment discrepancy，而不是只补视觉侧。
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: near-failure 样本更适合做 top1 分离训练与候选比较学习。
- Mind the Gap: Preserving and Compensating for the Modality Gap in CLIP-Based Continual Learning (ICCV 2025): https://openaccess.thecvf.com/content/ICCV2025/html/Huang_Mind_the_Gap_Preserving_and_Compensating_for_the_Modality_Gap_ICCV_2025_paper.html
  Reason: 持续学习时必须保护 modality gap，避免越学越偏。

Artifacts:
- E:\BISHE\video_retrieval_system\scripts\run_error_driven_agent_loop.py
- E:\BISHE\video_retrieval_system\scripts\build_self_feedback_supervision.py
- E:\BISHE\video_retrieval_system\scripts\update_continual_layer.py
- E:\BISHE\video_retrieval_system\论文方法设计稿草案.md

## 2026-04-24T16:40:00 | continual_layer::reference_protocol_fix

检查错误驱动闭环结果后确认：此前脚本把 `safe_dev` candidate 与锁定 `1kA` current best 直接比较，属于跨协议比较。现已修正为先对当前 best checkpoint 做 `safe_dev` 同协议参考评测，再进行 candidate 比较和晋升。

Decisions:
- 新增 `evaluate_checkpoint_adapter.py`，支持不训练、直接评估 checkpoint。
- `run_error_driven_agent_loop.py` 先生成 `safe_dev` reference summary，再比较 candidate。
- `1kA` 继续只作锁定汇报，不再直接参与 continual gate 比较。
- 这次看到的 `baseline=39` 属于 `safe_dev` 协议结果，不等于锁定 `1kA` 的 `50.5`。

Theory Support:
- Beyond Coarse-Grained Matching in Video-Text Retrieval (ACCV 2024): https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html
  Reason: 评测协议必须一致，否则指标比较会失真。
- C-CLIP: Multimodal Continual Learning for Vision-Language Model (ICLR 2025): https://openreview.net/forum?id=sb7qHFYwBc
  Reason: continual vision-language learning必须单独评估跨模态匹配与遗忘，不能混淆参考集。

Artifacts:
- E:\BISHE\video_retrieval_system\scripts\evaluate_checkpoint_adapter.py
- E:\BISHE\video_retrieval_system\scripts\run_error_driven_agent_loop.py

## 2026-04-24T16:20:29 | continual_layer::self_feedback_supervision

已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，把正样本与 hard negatives 写入 feedback memory 和下一轮 teacher supervision。

Decisions:
- Queries: 500
- Top1 is gt rate: 0.284
- Mean gt rank: 227.28
- Selected failed ranks: (1, 30]
- Selected rows: 201
- Selected gt rank mean: 7.880597
- Memory output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_feedback_memory.jsonl
- Teacher supervision output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_feedback_teacher.jsonl
- 仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_feedback_memory.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_feedback_teacher.jsonl

## 2026-04-24T16:20:36 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T16:21:36 | run_stage_experiment::stage3_error_driven_round01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=40.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.075
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_summary_quick_eval.json

## 2026-04-24T16:21:37 | continual_layer::state_update

Continual Layer 已启用：当前通过 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过当前最佳的 candidate 覆盖活动版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Active best metrics: {'R@1': 50.5, 'R@5': 64.5, 'R@10': 73.5, 'MnR': 20.42, 'MedR': 1.0}
- Candidate promoted: False; reason: Candidate did not beat current best R@1=50.5.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\round01_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json

## 2026-04-24T16:21:37 | continual_layer::error_driven_agent_loop

已完成错误驱动 agent 学习闭环：先从当前最优模型抽取 rank 2-30 的高价值失败样本，再构建 feedback teacher，warm-start 训练 candidate，并通过 promotion gate 决定是否晋升。

Decisions:
- Rounds: 1
- Feedback rank band: (1, 30]
- Promoted rounds: 0
- Final active summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- 该闭环只使用 safe_train 构建反馈、safe_dev 选模、1kA 仅作锁定汇报。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\loop_feedback.md
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_161939_error_driven_safe_dev\loop_feedback.json

## 2026-04-24T16:32:41 | continual_layer::self_feedback_supervision

已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，把正样本与 hard negatives 写入 feedback memory 和下一轮 teacher supervision。

Decisions:
- Queries: 500
- Top1 is gt rate: 0.284
- Mean gt rank: 227.28
- Selected failed ranks: (1, 30]
- Selected rows: 201
- Selected gt rank mean: 7.880597
- Memory output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_feedback_memory.jsonl
- Teacher supervision output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_feedback_teacher.jsonl
- 仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_feedback_memory.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_feedback_teacher.jsonl

## 2026-04-24T16:32:49 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-04-24T16:33:50 | run_stage_experiment::stage3_error_driven_round01

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=40.5, eval_queries=msrvtt_train_9k_safe_dev_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_train_9k_safe_dev_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.11
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.992
- Memory augmented weight: 0.075
- Teacher first candidates: True
- Teacher pairwise weight: 0.075
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.085
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.085
- Component alignment weight: 0.065
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: True
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.992/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_summary.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_summary.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_summary_quick_eval.json

## 2026-04-24T16:33:52 | continual_layer::state_update

Continual Layer 已启用：当前通过 acceptance-gated promotion 维护最优模型、memory 快照和后续晋升规则，不再让未超过当前最佳的 candidate 覆盖活动版本。

Decisions:
- Active best summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_summary.json
- Active best metrics: {'R@1': 40.5, 'R@5': 62.5, 'R@10': 72.0, 'MnR': 40.57, 'MedR': 2.0}
- Candidate promoted: True; reason: R@1 improved by 0.5000.
- State file: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_continual_state.json
- 后续新模型必须先作为 candidate 评测，再通过 R@1/MedR/MnR gate 晋升。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_continual_state.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_summary.json

## 2026-04-24T16:33:52 | continual_layer::error_driven_agent_loop

已完成错误驱动 agent 学习闭环：先对当前最优 checkpoint 在 safe_dev 上建立同协议参考，再抽取 rank 2-30 的高价值失败样本，构建 feedback teacher，warm-start 训练 candidate，并通过 promotion gate 决定是否晋升。

Decisions:
- Rounds: 1
- Feedback rank band: (1, 30]
- Promoted rounds: 1
- Locked report summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.json
- Safe-dev reference summary: E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\round01_summary.json
- 该闭环只使用 safe_train 构建反馈、safe_dev 选模、1kA 仅作锁定汇报。

Theory Support:
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm (WACV 2025): https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf
  Reason: One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\loop_feedback.md
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\error_driven_agent_loop\20260424_163109_error_driven_safe_dev\loop_feedback.json

## 2026-04-28T02:02:46 | stage_announcement::run_llm_pipeline

Entered Stage 1: System Optimization.

Decisions:
- Current responsibilities: baseline retrieval, query rewrite, candidate rerank
- Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.

## 2026-05-01T22:08:38 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-01T22:10:04 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-01T22:12:50 | run_stage_experiment::stage3_highquality_selected_componentview_vtokens6_align_multiview_pairwise_queryaware_q1500_eval1kAq200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=baseline, best_R1=49.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 20
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.1
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\alignment_teacher_highquality_selected_from_q1500_f6_v1.jsonl
- Alignment teacher weight: 0.1
- Multiview features: outputs\tables\analysis\multiview_features_highquality_selected_from_q1500_vtokens6_fpv2_v1.npz
- Multiview weight: 0.1
- Component alignment weight: 0.08
- Query-aware fusion: True
- Component-view weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.05
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 20/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality_selected_componentview_vtokens6_align_multiview_pairwise_queryaware_q1500_eval1kAq200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality_selected_componentview_vtokens6_align_multiview_pairwise_queryaware_q1500_eval1kAq200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality_selected_componentview_vtokens6_align_multiview_pairwise_queryaware_q1500_eval1kAq200_v1_quick_eval.json

## 2026-05-01T22:18:33 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-01T22:21:44 | run_stage_experiment::stage3_highquality500_vtokens6_componentview_preserve_r1_q1500_eval1kAq200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.2, best_method=baseline, best_R1=48.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.985
- Memory augmented weight: 0.04
- Teacher first candidates: True
- Teacher pairwise weight: 0.04
- Cross-modal video weight: 0.06
- Alignment teacher: outputs\tables\analysis\alignment_teacher_highquality_selected_from_q1500_f6_v1.jsonl
- Alignment teacher weight: 0.05
- Multiview features: outputs\tables\analysis\multiview_features_highquality_selected_from_q1500_vtokens6_fpv2_v1.npz
- Multiview weight: 0.06
- Component alignment weight: 0.04
- Query-aware fusion: False
- Component-view weight: 0.04
- Distill candidate topk: 24
- False negative margin: 0.03
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.985/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality500_vtokens6_componentview_preserve_r1_q1500_eval1kAq200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality500_vtokens6_componentview_preserve_r1_q1500_eval1kAq200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality500_vtokens6_componentview_preserve_r1_q1500_eval1kAq200_v1_quick_eval.json

## 2026-05-01T22:33:49 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-01T22:35:10 | run_stage_experiment::stage3_highquality_selected_q1500_replay_v35_recipe_eval1kAq200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=49.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.08
- Teacher first candidates: True
- Teacher pairwise weight: 0.06
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Query-aware fusion: False
- Component-view weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.02
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: True
- Acceptance thresholds rank/uncertainty/overlap: 12/0.995/0.0
- Acceptance alignment weight: 1.0
- Acceptance use as filter: True
- Init checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality_selected_q1500_replay_v35_recipe_eval1kAq200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality_selected_q1500_replay_v35_recipe_eval1kAq200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage3_highquality_selected_q1500_replay_v35_recipe_eval1kAq200_v1_quick_eval.json

## 2026-05-01T23:02:04 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-03T18:15:04 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-03T18:17:17 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-03T18:20:37 | run_stage_experiment::continual_nearmiss_rank2_5_from_v35_pairwise_eval1kAq200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.25, best_method=adapter, best_R1=48.5, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 12
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.14
- Cross-modal video weight: 0.08
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.08
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.08
- Component alignment weight: 0.0
- Query-aware fusion: False
- Component-view weight: 0.0
- Distill candidate topk: 24
- False negative margin: 0.03
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False
- Init checkpoint: outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt
- Selective rank checkpoint: outputs\tables\analysis\stage3_alignment_multiview_v35_1kA_train500_eval200_gpu_v1.pt

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_nearmiss_rank2_5_from_v35_pairwise_eval1kAq200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_nearmiss_rank2_5_from_v35_pairwise_eval1kAq200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\continual_nearmiss_rank2_5_from_v35_pairwise_eval1kAq200_v1_quick_eval.json

## 2026-05-04T17:17:12 | continual_layer::self_feedback_supervision

已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，把正样本与 hard negatives 写入 feedback memory 和下一轮 teacher supervision。

Decisions:
- Queries: 500
- Top1 is gt rate: 0.286
- Mean gt rank: 228.078
- Selected failed ranks: (1, 30]
- Selected rows: 200
- Selected gt rank mean: 7.98
- Memory output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\xcot_style_pairwise_feedback_memory_q500_v1.jsonl
- Teacher supervision output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\xcot_style_pairwise_feedback_teacher_q500_v1.jsonl
- 仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\xcot_style_pairwise_feedback_memory_q500_v1.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\xcot_style_pairwise_feedback_teacher_q500_v1.jsonl

## 2026-05-04T17:20:31 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T17:22:08 | run_stage_experiment::stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAq200_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=49.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 30
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.16
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.1
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.1
- Component alignment weight: 0.08
- Query-aware fusion: True
- Component-view weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.05
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False
- Init checkpoint: none
- Selective rank checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAq200_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAq200_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAq200_v1_quick_eval.json

## 2026-05-04T17:25:24 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T17:36:21 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T17:43:52 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T17:46:15 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T17:55:21 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T17:59:37 | run_stage_experiment::stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAfull_lowmem_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=39.1, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 30
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.16
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.1
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.1
- Component alignment weight: 0.08
- Query-aware fusion: True
- Component-view weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.05
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False
- Init checkpoint: none
- Selective rank checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAfull_lowmem_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAfull_lowmem_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage4_queryaware_multiview_attention_pairwise_teacher_q500_eval1kAfull_lowmem_v1_quick_eval.json

## 2026-05-04T18:30:33 | continual_layer::self_feedback_supervision

已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，把正样本与 hard negatives 写入 feedback memory 和下一轮 teacher supervision。

Decisions:
- Queries: 500
- Top1 is gt rate: 0.324
- Mean gt rank: 181.954
- Selected failed ranks: (1, 5]
- Selected rows: 118
- Selected gt rank mean: 2.898305
- Memory output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_5_error_type_component_memory_q500_v1.jsonl
- Teacher supervision output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_5_error_type_component_teacher_q500_v1.jsonl
- 仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_5_error_type_component_memory_q500_v1.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_5_error_type_component_teacher_q500_v1.jsonl

## 2026-05-04T18:31:19 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T18:35:29 | run_stage_experiment::stage5_querygate_errortype_component_teacher_rank2_5_q500_eval1kAfull_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=38.7, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 5
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.18
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.1
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.1
- Component alignment weight: 0.1
- Query-aware fusion: True
- Component-view weight: 0.1
- Distill candidate topk: 24
- False negative margin: 0.05
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False
- Init checkpoint: none
- Selective rank checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_querygate_errortype_component_teacher_rank2_5_q500_eval1kAfull_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_querygate_errortype_component_teacher_rank2_5_q500_eval1kAfull_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_querygate_errortype_component_teacher_rank2_5_q500_eval1kAfull_v1_quick_eval.json

## 2026-05-04T18:38:28 | continual_layer::self_feedback_supervision

已构建自学习反馈监督：当前 agent 先在 safe_train 检索，再与正确 gt 对比，把正样本与 hard negatives 写入 feedback memory 和下一轮 teacher supervision。

Decisions:
- Queries: 500
- Top1 is gt rate: 0.324
- Mean gt rank: 181.954
- Selected failed ranks: (1, 10]
- Selected rows: 154
- Selected gt rank mean: 3.954545
- Memory output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_10_soft_errortype_component_memory_q500_v1.jsonl
- Teacher supervision output: E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_10_soft_errortype_component_teacher_q500_v1.jsonl
- 仅使用 safe_train 的 gt 构建反馈监督，避免 1kA 测试集泄露。

Theory Support:
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_10_soft_errortype_component_memory_q500_v1.jsonl
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_nearmiss_rank2_10_soft_errortype_component_teacher_q500_v1.jsonl

## 2026-05-04T18:39:38 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T18:43:53 | run_stage_experiment::stage5_soft_querygate_errortype_component_rank2_10_q500_eval1kAfull_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=39.0, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.08
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 10
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.1
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.1
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.1
- Component alignment weight: 0.06
- Query-aware fusion: True
- Component-view weight: 0.06
- Distill candidate topk: 24
- False negative margin: 0.04
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False
- Init checkpoint: none
- Selective rank checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_soft_querygate_errortype_component_rank2_10_q500_eval1kAfull_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_soft_querygate_errortype_component_rank2_10_q500_eval1kAfull_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage5_soft_querygate_errortype_component_rank2_10_q500_eval1kAfull_v1_quick_eval.json

## 2026-05-04T19:18:50 | stage_announcement::run_stage_experiment

Entered Stage 3: Continual Learning and Memory.

Decisions:
- Current responsibilities: prototype memory, hard negative memory, constraint memory, acceptance-gated continual learning
- Focus on prototype memory, hard negative memory, constraint memory, and acceptance-gated continual learning.

## 2026-05-04T19:24:13 | run_stage_experiment::stage6_btstyle_temporal_adapter_q500_eval1kAfull_v1

Completed a Stage 2 training round with adapter_mode=gated, residual_scale=0.35, best_method=adapter, best_R1=39.1, eval_queries=msrvtt_1kA_test_queries.jsonl.

Decisions:
- Train queries: msrvtt_train_9k_safe_train_queries.jsonl
- Quick-gate eval queries: msrvtt_1kA_test_queries.jsonl
- Teacher supervision source: external_teacher_supervision
- Hard negative mode: teacher_hybrid
- Teacher temperature: 0.07
- Prototype teacher weight: 0.08
- Structured prototype weight: 0.1
- Video aggregation weight: 0.2
- Teacher reliability gating: True
- Teacher max gt rank: 30
- Teacher min margin: 0.003
- Teacher max uncertainty: 0.995
- Memory augmented weight: 0.0
- Teacher first candidates: True
- Teacher pairwise weight: 0.16
- Cross-modal video weight: 0.1
- Alignment teacher: outputs\tables\analysis\multiframe_alignment_teacher_train_q500_targets_plus_1kA_f6_v33.jsonl
- Alignment teacher weight: 0.1
- Multiview features: outputs\tables\analysis\multiview_features_train_q500_targets_plus_1kA_fpv2_v35.npz
- Multiview weight: 0.1
- Component alignment weight: 0.08
- Query-aware fusion: True
- Component-view weight: 0.08
- Distill candidate topk: 24
- False negative margin: 0.05
- Uncertainty-aware temperature: False
- Teacher temperature min/max: 0.05/0.11
- Stage key: stage3
- Acceptance-gated memory: False
- Acceptance thresholds rank/uncertainty/overlap: 10/0.98/0.0
- Acceptance alignment weight: 0.0
- Acceptance use as filter: False
- Init checkpoint: none
- Selective rank checkpoint: none

Theory Support:
- ViCLIP / InternVid (ICLR 2024): https://openreview.net/forum?id=MLBdiWu4Fw
  Reason: Use a strong video-text teacher while keeping the student retrieval path cheap.
- Holistic Features are almost Sufficient for Text-to-Video Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html
  Reason: Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.
- MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval (CVPR 2024): https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html
  Reason: Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.
- DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html
  Reason: Language-side and alignment-side adaptation matter in addition to video-side transfer.

Artifacts:
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage6_btstyle_temporal_adapter_q500_eval1kAfull_v1.json
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage6_btstyle_temporal_adapter_q500_eval1kAfull_v1.pt
- E:\BISHE\video_retrieval_system\outputs\tables\analysis\stage6_btstyle_temporal_adapter_q500_eval1kAfull_v1_quick_eval.json
