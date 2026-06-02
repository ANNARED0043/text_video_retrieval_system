# Project Todo And Thesis Guide

## 1. Current Project Goal

- Main target:
  push the current `ViT-H-14 / laion2b_s32b_b79k` baseline on `MSRVTT 1kA`
  from `R@1 = 47.0` toward `R@1 >= 60`
- Core strategy:
  use `msrvtt_train_9k` for staged distillation and memory-assisted learning,
  and use `1kA 200-query` as the fast gate before promoting runs to full
  `1kA`
- Current practical route:
  stay lightweight first, keep baseline candidate retrieval compact, and only
  add heavier teacher signals after a Stage 1 quick-gate win

## 2. Current Repository Structure

### Root

- `README.md`
  overall project description and usage entry
- `AGENTS.md`
  local engineering rules for this repository
- `todo.md`
  this project and thesis guidance document
- `19220717赵月论文.doc`
  thesis writing file provided in the workspace

### Data / Experiment Assets

- `data/raw_videos/`
  current raw video storage
- `data/features/`
  extracted video features
- `data/indexes/`
  FAISS retrieval indexes
- `data/cache/`
  teacher-side cache, especially `ViCLIP` video features
- `outputs/`
  experiment summaries, evaluation outputs, checkpoints, diary, and figures

### Docs

- `docs/technical_stage_notes.md`
  technical experiment log, research references, stage notes
- `docs/remote_training_runbook.md`
  staged runbook and acceptance-gate execution notes

### Scripts

- `scripts/extract_features.py`
  full feature extraction
- `scripts/build_index.py`
  FAISS index building
- `scripts/eval_msrvtt.py`
  baseline retrieval evaluation on `1kA`
- `scripts/eval_candidate_recall.py`
  single-`k` candidate recall evaluation
- `scripts/eval_candidate_recall_sweep.py`
  candidate recall curve sweep and plotting
- `scripts/build_viclip_teacher_supervision.py`
  true `ViCLIP` teacher supervision generation
- `scripts/run_stage_experiment.py`
  lightweight student training + quick evaluation
- `scripts/run_stage1_light_pipeline.py`
  automated light Stage 1 pipeline:
  candidate recall -> teacher build -> training -> quick gate
- `scripts/check_acceptance_gate.py`
  quick/full gate checker
- `scripts/run_rerank_eval.py`
  rerank evaluation pipeline

### Source Code

- `src/features/clip_encoder.py`
  baseline CLIP / OpenCLIP text encoding path
- `src/features/viclip_encoder.py`
  real `ViCLIP` loading and encoding path
- `src/retrieval/searcher.py`
  FAISS search wrapper
- `src/retrieval/index_builder.py`
  index construction logic
- `src/evaluation/evaluator_msrvtt.py`
  `1kA` evaluation with `tqdm`
- `src/learning/teacher_supervision.py`
  teacher target definitions and I/O
- `src/learning/text_adapter.py`
  current lightweight student adapter training logic
- `src/llm/semantic_memory.py`
  prototype and constraint memory utilities
- `src/llm/policy_learning.py`
  policy hint loading and related logic

## 3. Current File And Artifact Status

### Data Preparation

- `MSRVTT_Videos.zip` has been unpacked
- `data/raw_videos/msrvtt` now contains the full `10000` videos
- old partial video folder was backed up before replacement
- Linux-compatible video-level manifests were rebuilt

### Feature And Index Status

- full `msrvtt_fixed` `ViT-H` features have been extracted
- full `msrvtt_fixed` FAISS index has been built
- `1kA` baseline evaluation is reproducible in the current environment

### Baseline Status

- verified baseline:
  `R@1 47.0 / R@5 65.0 / R@10 72.0`
- baseline artifact:
  [baseline_vith14_mean_topk200_max_N200_recheck.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_mean_topk200_max_N200_recheck.json)

### Candidate Recall Status

- single `topk=30` full-`1kA` candidate recall was measured
- full curve for `k = 1, 5, 10, 20, 30, 40, 50` was measured and plotted
- curve artifacts:
  [baseline_vith14_candidate_recall_curve_1kA_full.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_candidate_recall_curve_1kA_full.json)
  and
  [baseline_vith14_candidate_recall_curve_1kA_full.png](E:/BISHE/video_retrieval_system/outputs/figures/baseline_vith14_candidate_recall_curve_1kA_full.png)

### Teacher Status

- true `ViCLIP` integration is working
- `ViCLIP` teacher can generate:
  text-video similarity targets
  listwise targets
  hard negatives
- small q200 teacher and light Stage 1 teacher artifacts already exist

### Logging / Experiment Tracking

- experiment diary:
  [learning_diary.jsonl](E:/BISHE/video_retrieval_system/outputs/feedback/learning_diary.jsonl)
- technical notes:
  [technical_stage_notes.md](E:/BISHE/video_retrieval_system/docs/technical_stage_notes.md)
- runbook:
  [remote_training_runbook.md](E:/BISHE/video_retrieval_system/docs/remote_training_runbook.md)

## 4. What Has Been Completed

### Engineering Side

- repaired repository write capability in the current Linux environment
- unpacked and switched to full `10000` video set
- rebuilt Linux-compatible manifests
- extracted full `ViT-H` features
- built full FAISS index
- rechecked `1kA 200-query` baseline
- added a true `ViCLIP` encoder path
- added `ViCLIP` teacher supervision generation
- added acceptance-gate scripts
- added candidate-recall evaluation scripts
- added candidate-recall curve plotting script
- added a lightweight Stage 1 automation pipeline
- added progress visualization with `tqdm` for long-running teacher generation

### Experimental Side

- verified current baseline is stable and matches the reference result
- verified `topk=30` candidate recall on full `1kA`
- generated `ViCLIP` teacher supervision on compact candidate sets
- ran at least two lightweight Stage 1 attempts and recorded them

## 5. What Has Been Tried

### Attempt A: Bootstrap Teacher

- teacher source:
  bootstrap `ViT-H` retrieval, not true `ViCLIP`
- result:
  failed badly
- effect:
  adapter collapsed, fusion also failed to beat baseline
- conclusion:
  not suitable as main Stage 1 direction

### Attempt B: ViCLIP Top-k30 Lightweight Stage 1

- setup:
  `student_topk=30`, `teacher_topk=10`, `max_train_queries=2000`,
  `max_eval_queries=200`, one adapter epoch
- result:
  baseline remained best
- conclusion:
  true `ViCLIP` teacher is connected, but current adapter training still harms
  ranking quality

### Attempt C: ViCLIP Top-k30 Tuned V1

- change:
  lower teacher weights, disable late interaction, use more conservative fusion
- result:
  more stable than Attempt B, but still below baseline
- conclusion:
  parameter-only reduction helps stability but does not yet deliver gains

## 6. Key Findings So Far

### Finding 1: Baseline Is Correct And Stable

- current `ViT-H` baseline is reproducible
- this is now a reliable comparison anchor

### Finding 2: Top-k30 Is A Reasonable First Choice

- candidate recall curve shows:
  gains after `k=30` become noticeably smaller
- current curve:
  `k=20 -> 30` gives `+3.80`
  `k=30 -> 40` gives `+2.58`
  `k=40 -> 50` gives `+1.94`
- project implication:
  `k=30` is a good current tradeoff between headroom and cost

### Finding 3: Current Adapter Is Too Aggressive

- in multiple runs, the adapter ranking quality falls below baseline
- fused variants can partially recover but still do not clear the gate
- project implication:
  next gains are more likely to come from a more conservative student update
  design than from simply increasing teacher supervision strength

### Finding 4: True ViCLIP Is Technically Ready

- `ViCLIP` can now be used as the main embedding teacher
- the bottleneck has moved from model loading to training design and objective
  quality

## 7. What Still Needs To Be Done

### Immediate Todo

- redesign Stage 1 to be more conservative than the current text adapter
- test lower residual strength or gated adapter behavior
- test teacher usage that affects fusion/rerank more than base embedding
- test candidate-limited listwise distillation before heavier frame signals
- keep all new trials gated by `1kA 200-query`

### Mid-term Todo

- implement a cleaner `ViC-style top-20 listwise` loss within the candidate set
- bucket hard queries and only apply stronger teacher signals there
- refine semantic memory so it acts as a sampler before acting as a loss source
- add an experiment table exporter for later paper figures
- add more polished visualization assets for the web interface

### Later Todo

- once a Stage 1 win appears, promote to full `1kA`
- then implement Stage 2 selective frame relevance teacher
- then implement Stage 2 selective late interaction teacher
- finally implement Stage 3 memory refresh under acceptance gate

## 8. Recommended Next Technical Route

### Route A: Conservative Stage 1 Redesign

- keep `k=30`
- keep `teacher_topk=10`
- reduce student update strength even further
- prioritize weak listwise guidance and safer fusion over aggressive adapter
  movement

### Route B: ViC-style Candidate Listwise Distillation

- use the current baseline candidate set as the training universe
- only distill top-ranked candidate distributions
- do not attempt full-library teacher matching
- this is closer to lightweight reranking than heavy backbone retraining

### Route C: Hard-Query Selective Supervision

- identify queries where baseline rank is between:
  `2~30`
- these are the most promising queries for reranking gain
- apply stronger teacher signals only there
- skip easy positives and hopeless misses in early stages

### Route D: Memory As Sampler First

- Stage 3 should not be introduced as a full heavy memory loss system first
- use memory for:
  hard query selection
  high-value hard negatives
  prototype grouping
- only later consider making memory part of auxiliary losses

## 9. Techniques Already Used Or Referenced

### Already Used In Code Or Experiments

- `ViT-H-14 / laion2b_s32b_b79k` baseline retrieval
- FAISS flat inner-product search
- true `ViCLIP` teacher reranking over baseline candidates
- hard negative mining
- prototype-aware bonus
- constraint-memory-assisted bonus
- lightweight text residual adapter
- candidate recall curve measurement
- acceptance gate on `1kA 200-query`

### Main Technical Ideas For Future Use

- `ViCLIP` as the main embedding teacher
- `ViC-style` top-list soft-label distillation within candidate sets
- selective frame relevance teacher
- selective late interaction teacher
- acceptance-gated continual memory refresh

### Research Ideas Already Written Into Notes

- `ViCLIP`
- `ColBERT`-style late interaction
- ranking distillation
- lossless / self-distilled neural ranking

## 10. Thesis Writing Plan: Chapters 1-3

### Chapter 1: Introduction

#### What to write

- research background:
  text-video retrieval, video understanding, multimodal retrieval
- practical problem:
  current baseline is strong but `R@1` remains limited
- contradiction:
  stronger teachers often improve supervision quality, but full heavy
  distillation is expensive and hard to deploy
- project motivation:
  explore whether a lightweight, staged teacher-guided retrieval enhancement
  framework can improve `MSRVTT 1kA` retrieval while controlling cost
- main research objective:
  improve `R@1 / R@5 / R@10`, especially `R@1`, under a practical and
  reproducible pipeline

#### Chapter 1 key points

- why video-text retrieval matters
- what the bottleneck is in current CLIP-style video retrieval
- why direct heavy training is not ideal
- why staged and candidate-limited distillation is attractive
- what this thesis attempts to solve
- what the main contributions are

#### Suggested contribution wording

- built a reproducible `ViT-H` baseline and full feature-index pipeline on
  `MSRVTT`
- introduced a true `ViCLIP` teacher path for candidate-limited supervision
- proposed a lightweight staged optimization route based on candidate recall and
  acceptance gating
- analyzed the effect of candidate set size through a full `topk` recall curve

### Chapter 2: Related Work

#### What to write

- text-video retrieval methods
- CLIP / OpenCLIP style retrieval representations
- video-language pretraining
- ranking distillation and listwise supervision
- late interaction retrieval
- memory-assisted learning and hard negative mining

#### Recommended section breakdown

- 2.1 Text-video retrieval and video representation learning
- 2.2 CLIP-style retrieval and transferable multimodal embeddings
- 2.3 Teacher-student distillation for ranking and retrieval
- 2.4 Listwise supervision and reranking
- 2.5 Memory and hard-negative based retrieval optimization

#### Writing guidance

- do not just list papers
- each subsection should answer:
  what problem the line of work solves
  what advantage it gives
  what limitation remains
  how this thesis borrows or adapts the idea

#### For this project specifically

- `ViCLIP`:
  explain why it is chosen as the main teacher rather than as the student
- `ViC-style listwise`:
  explain that the thesis uses the idea of soft ranking supervision inside a
  compact candidate set
- `ColBERT` / late interaction:
  explain it as a selective later-stage teacher idea, not necessarily as the
  main retrieval architecture

### Chapter 3: Method

#### What to write

- overall pipeline
- dataset protocol
- baseline construction
- feature extraction and indexing
- candidate recall analysis and top-k selection
- Stage 1, Stage 2, Stage 3 design
- acceptance gate and experiment management

#### Recommended section breakdown

- 3.1 Problem definition and task formulation
- 3.2 Dataset and evaluation protocol
- 3.3 Baseline retrieval system
- 3.4 Candidate-recall-guided top-k selection
- 3.5 Stage 1 lightweight teacher-guided distillation
- 3.6 Stage 2 richer supervision extension
- 3.7 Stage 3 memory-assisted continual refinement
- 3.8 Acceptance gate and experiment workflow

#### Chapter 3 writing highlights

- describe the baseline first:
  `ViT-H` feature extraction -> FAISS retrieval -> video-level aggregation ->
  `1kA` evaluation
- then explain why candidate recall matters:
  reranking can only help if the correct video is already in the retrieved
  candidate set
- use the `topk` recall curve to justify `k=30`
- then describe Stage 1 as the first practical enhancement layer:
  `ViCLIP` teacher on baseline candidates
- explain why Stage 2 is delayed:
  stronger teachers are more expensive and should only be added after Stage 1
  proves effective
- explain why Stage 3 uses acceptance gating:
  to avoid degrading the current best model

#### What figures chapter 3 should eventually include

- overall system framework diagram
- baseline retrieval pipeline diagram
- candidate recall curve (`k=1,5,10,20,30,40,50`)
- Stage 1/2/3 training flow chart
- acceptance gate flow chart

## 11. Suggested Writing Strategy For The Thesis

- First finish Chapter 1 and Chapter 2 in full text
- For Chapter 3, write the framework and current implemented parts first
- clearly separate:
  implemented and verified modules
  proposed but not yet completed modules
- for unfinished later-stage items, write them as:
  planned extension directions or staged design, unless they are fully
  implemented and experimentally verified

## 12. Suggested Next Engineering Todo

- [ ] redesign Stage 1 student update to be more conservative than current
      residual adapter
- [ ] test lower residual scale or gated residual adapter
- [ ] test candidate-set-only listwise weak supervision
- [ ] test selective hard-query training subset
- [ ] test safer fusion-only improvement before deeper distillation
- [ ] if any quick gate run exceeds `R@1 > 48`, promote to full `1kA`
- [ ] after a stable Stage 1 win, start selective Stage 2 teacher integration
- [ ] prepare experiment tables and visuals for paper figures and the web UI

## 13. 论文第一章到第三章详细写作稿与写作指引

说明：

- 以下内容按照论文文档当前目录标题来写
- 当前目录主线为：
  第1章 绪论
  第2章 相关理论与关键技术
  第3章 基于自然语言查询的视频检索方法
- 写作时建议保持“已经实现并验证的内容”和“后续规划内容”分开表述
- 对于尚未完成的 Stage 2 / Stage 3，不要写成已经取得最终效果，而应写成方法设计与预期优化方向

### 第1章 绪论

#### 1.1 研究背景与研究意义

##### 1.1.1 视频检索技术的发展背景

可直接写作思路：

随着短视频平台、在线视频网站以及教育、安防、医疗等行业视频数据的快速增长，海量视频内容已成为互联网信息的重要组成部分。与图像和文本数据相比，视频不仅包含空间视觉信息，还包含时间动态变化，因此其语义结构更加复杂，检索难度更高。如何从大规模视频数据中高效、准确地检索出与用户需求相匹配的内容，已经成为多媒体信息检索领域的重要研究方向。

早期视频检索方法通常依赖人工标签、关键词匹配或低层视觉特征检索。这类方法在数据规模较小、语义需求较简单的场景中具有一定效果，但当用户查询表达变得更丰富、更抽象时，传统方法难以准确捕获视频内容中的高层语义信息。近年来，随着深度学习、多模态表示学习和大语言模型的发展，基于自然语言查询的视频检索逐渐成为研究热点。该任务允许用户直接通过自然语言描述检索目标视频，能够显著提升系统的易用性和人机交互自然度。

建议插图：

- 图1-1 视频检索任务发展示意图
  内容建议：从“关键词检索/人工标签检索”演化到“深度特征检索”再到“自然语言驱动视频检索”
- 图1-2 视频检索应用场景图
  内容建议：短视频平台、教育视频检索、监控事件回溯、智能媒体资产管理

建议引用：

- 视频检索综述类文献
- 多模态检索综述类文献
- CLIP / VideoCLIP / ViCLIP 等代表性工作

##### 1.1.2 自然语言查询视频检索的应用价值

可直接写作思路：

自然语言查询视频检索能够降低用户的使用门槛，使用户无需掌握检索系统内部标签体系或特定检索语法，只需要使用日常语言描述目标内容即可完成检索。例如，用户可以输入“一个人在海边奔跑”“小狗在草地上玩耍”或“有人在厨房里切菜”等自然语言描述，系统需要自动理解文本语义并在视频数据库中找到最相关的视频结果。

这种检索方式在多个实际场景中具有明显应用价值。对于短视频平台，自然语言查询能够改善内容发现与推荐体验；对于教育与知识管理平台，可以帮助用户快速定位教学片段；对于安防与公共服务场景，可以加速事件回溯；对于媒体资源管理系统，则可以显著降低人工标注和人工筛查成本。因此，研究基于自然语言查询的视频检索系统，不仅具有理论研究意义，也具有较强的工程应用价值。

建议插图：

- 图1-3 自然语言查询视频检索应用场景图
  内容建议：用户输入文本，系统返回相关视频列表

建议引用：

- 自然语言视频检索代表任务论文
- 实际场景中的多媒体检索应用论文或报告

##### 1.1.3 当前视频检索面临的主要问题

可直接写作思路：

尽管基于深度学习的视频检索方法取得了明显进展，但在实际系统落地中仍面临多个问题。首先，视频数据具有时序性和内容冗余性，如何在保持语义表达能力的同时控制计算和存储成本，是系统设计中的关键难点。其次，自然语言查询本身具有多义性和模糊性，不同用户可能使用不同表达方式描述相同的视频内容，从而导致查询与视频内容之间存在语义偏差。再次，即使基于向量检索能够快速召回候选结果，候选视频之间的细粒度语义差异仍然难以准确区分，这会限制系统的最终排序效果。

此外，大语言模型虽然为查询改写和结果重排序提供了新的解决思路，但其引入也带来了成本、时延、缓存管理以及调用策略设计等问题。如果对所有查询都直接调用大语言模型，不仅计算成本高，也未必能够带来稳定收益。因此，如何在检索效果、系统复杂度和工程可行性之间取得平衡，是当前自然语言视频检索系统研究中的重要问题。

建议插图：

- 图1-4 当前系统面临问题示意图
  内容建议：数据规模大、查询歧义、候选排序困难、LLM 成本高

建议引用：

- 视频理解与检索中的语义鸿沟相关文献
- LLM 检索增强与 rerank 成本分析相关文献

##### 1.1.4 本文研究内容与研究意义

可直接写作思路：

针对上述问题，本文围绕“基于自然语言查询的视频检索系统设计与实现”展开研究，基于 MSR-VTT 数据集构建一个从视频预处理、特征提取、向量索引、候选召回到查询改写与候选重排序的完整实验与系统实现流程。具体而言，本文首先构建多模态视频检索 baseline，验证自然语言到视频的基础检索能力；随后引入选择性查询改写机制，利用歧义检测模块判断是否需要调用大语言模型对原始查询进行改写或扩展；在此基础上，再设计候选结果重排序模块，对初始召回结果进行更细粒度的语义排序优化。

在当前项目推进中，还进一步探索了基于 `ViCLIP` teacher 的轻量化蒸馏增强路线，希望在保持工程可行性的前提下，从现有 baseline 出发逐步提高 `R@1 / R@5 / R@10`，特别是将 `R@1` 从当前约 `47` 提升到更高水平。本文的研究意义主要体现在两个方面：一是从工程实现角度验证自然语言驱动视频检索系统的可行性与可扩展性；二是从方法设计角度探索轻量级 teacher-guided 优化策略在视频检索任务中的应用潜力。

建议插图：

- 图1-5 本文研究内容总览图
  内容建议：Baseline 检索、Query Rewrite、Rerank、Stage 1-3 轻量优化路线

建议引用：

- MSR-VTT 数据集论文
- FAISS
- OpenCLIP / ViT-H
- ViCLIP

#### 1.2 国内外研究现状

##### 1.2.1 传统视频检索方法研究现状

可直接写作思路：

传统视频检索方法主要依赖人工标签、文本元数据、关键帧检索以及低层视觉特征匹配。这类方法的核心思路是在视频数据中提取颜色、纹理、边缘、局部描述子等特征，再通过相似度匹配实现视频检索。尽管此类方法在特定受控场景中具有一定效果，但其主要不足在于难以表达复杂语义信息，尤其难以处理自然语言查询中的抽象描述和事件语义。

随着深度学习的发展，卷积神经网络逐步取代传统手工特征，视频检索开始从低层特征匹配向深层语义表示学习转变。然而，传统方法奠定了视频分段、关键帧提取、特征索引与近似搜索等工程基础，这些思想在当前系统中仍然具有参考价值。

建议插图：

- 图1-6 传统视频检索方法示意图

建议引用：

- 传统 CBVR 或视频检索经典综述

##### 1.2.2 跨模态视频文本检索研究现状

可直接写作思路：

跨模态视频文本检索是近年来的研究重点，其目标是将文本查询与视频内容映射到统一或可比较的语义表示空间中，通过跨模态相似度实现检索。早期方法多使用双塔结构分别编码文本和视频，再通过对比学习或排序损失进行训练。随着 CLIP、VideoCLIP、X-CLIP、ViCLIP 等工作的出现，多模态表示学习能力显著增强，文本与视觉内容之间的对齐效果得到提升。

这类方法的优势在于能够较好地支持自然语言驱动的检索任务，但在实际大规模系统中仍面临候选召回与精排之间的矛盾：直接进行全量高精度匹配成本较高，而仅依赖向量粗召回又难以保证最终排序质量。因此，当前很多研究开始采用“两阶段”思路，即先用高效向量检索做候选召回，再用更强模型进行重排序或蒸馏增强。

建议插图：

- 图1-7 跨模态视频文本检索发展路线图

建议引用：

- CLIP
- VideoCLIP
- X-CLIP
- ViCLIP
- MSR-VTT benchmark 代表论文

##### 1.2.3 大语言模型增强检索研究现状

可直接写作思路：

随着大语言模型在语义理解和生成任务中的表现不断提升，其在信息检索领域中的辅助作用也受到广泛关注。相关研究主要集中在三类方向：查询改写、检索增强和结果重排序。对于自然语言视频检索任务，大语言模型可以帮助系统分析原始查询中的歧义信息、补充上下文语义、扩展潜在描述词，并对候选结果进行更高层次的语义判断。

然而，大语言模型增强检索也存在一些限制。首先，模型调用成本和响应时延较高，不适合无差别地对所有查询和所有候选结果进行处理；其次，大语言模型生成结果具有一定不稳定性，可能引入噪声；再次，如果缺乏合理的缓存和调用控制策略，系统整体复杂度会迅速增加。因此，当前研究趋势之一是选择性调用与轻量化集成，即仅在有必要时使用 LLM 对检索流程进行增强。

建议插图：

- 图1-8 大语言模型增强检索方式示意图
  内容建议：查询改写、候选重排序、缓存与调用控制

建议引用：

- LLM for IR / RAG / reranking 相关论文
- 查询改写与 rerank 代表工作

#### 1.3 本文主要研究内容

##### 1.3.1 多模态视频检索 baseline 的构建

写作要点：

- 基于 MSR-VTT 构建视频检索 baseline
- 使用视频分段、视觉特征提取、时序聚合、FAISS 检索和视频级聚合
- 当前验证结果为 `R@1 47.0 / R@5 65.0 / R@10 72.0`
- baseline 既是系统基础，也是后续增强方法的比较对象

##### 1.3.2 选择性查询改写方法设计

写作要点：

- 不是对所有查询都调用大语言模型
- 先做查询歧义检测
- 对高歧义或高价值查询进行改写或扩展
- 平衡效果与成本

##### 1.3.3 基于大语言模型的候选结果重排序

写作要点：

- 在 baseline 召回结果上进行语义重排
- 重排不是替代召回，而是提高候选结果区分能力
- 当前系统支持对候选视频进行语义评分和重排
- 后续还扩展到 `ViCLIP` teacher + 轻量蒸馏的思路

##### 1.3.4 系统实现与实验评估方案

写作要点：

- 完整实现命令行实验流程与系统模块
- 评估 baseline、rewrite、rerank、teacher-guided light stage
- 指标包括 `R@1 / R@5 / R@10 / MedR / MnR`
- 同时分析开销、响应速度、缓存与实验组织方式

#### 1.4 本文组织结构

可直接写作思路：

本文共分为五章。第一章为绪论，介绍研究背景、研究意义、国内外研究现状以及本文的主要研究内容。第二章为相关理论与关键技术，主要介绍视频检索任务、视频特征表示、向量检索技术以及大语言模型辅助检索相关方法。第三章为基于自然语言查询的视频检索方法，重点介绍本文提出的整体方法框架、基线检索方法、选择性查询改写方法、候选结果重排序方法以及实验方案设计。第四章为系统设计与实现，说明系统架构、模块划分、开发环境与实验环境。第五章为系统测试与分析，对实验结果进行分析与总结。

建议插图：

- 图1-9 论文结构示意图

---

### 第2章 相关理论与关键技术

#### 2.1 视频检索任务定义与评价方式

##### 2.1.1 文本到视频检索任务定义

可直接写作思路：

文本到视频检索任务的目标是在给定自然语言查询的条件下，从视频库中检索出与该文本语义最相关的视频。形式化地说，给定查询集合 `Q` 和视频集合 `V`，系统需要学习一个相似度函数 `s(q, v)`，使得与查询匹配的视频在排序结果中尽可能靠前。该任务本质上属于跨模态检索问题，需要解决文本语义与视觉内容之间的表示对齐问题。

建议插图：

- 图2-1 文本到视频检索任务定义图

建议引用：

- 文本视频检索经典任务论文

##### 2.1.2 视频片段级与视频级检索表示

可直接写作思路：

由于原始视频通常较长且内容变化丰富，直接将整段视频作为单一输入可能会导致语义表达不充分。为此，实际系统通常先将视频划分为若干片段，对每个片段分别提取特征，然后再通过时序聚合或视频级聚合得到最终表示。在检索阶段，也可以先进行片段级召回，再通过最大值聚合或其他方式形成视频级排序结果。当前系统采用的就是“片段特征 + 视频级聚合”的实现思路。

建议插图：

- 图2-2 片段级表示与视频级表示关系图

##### 2.1.3 检索评价指标

可直接写作思路：

视频检索任务常用评价指标包括 `Recall@K`、中位排序 `MedR` 和平均排序 `MnR`。其中，`Recall@1` 表示正确视频排在第 1 位的比例，能够反映系统首结果的准确性；`Recall@5` 和 `Recall@10` 则反映系统在前几个候选中的命中能力；`MedR` 和 `MnR` 用于衡量整体排序质量。本文重点关注 `R@1` 的提升，同时兼顾 `R@5` 与 `R@10` 的变化。

建议插图：

- 图2-3 检索指标示意图
  内容建议：同一查询下排序位置与 R@K 的关系

建议引用：

- MSR-VTT 评测协议或相关 benchmark 论文

#### 2.2 视频特征表示相关技术

##### 2.2.1 视频片段划分方法

可直接写作思路：

视频片段划分是视频检索系统中的重要预处理环节。合理的片段划分能够在保留语义连续性的同时减少冗余信息。常见方法包括固定时长切分、镜头边界切分以及基于内容变化的自适应切分。当前系统主要采用固定片段划分方案，其优点是实现简单、流程稳定，并适合大规模特征提取与索引构建。

建议插图：

- 图2-4 视频切分流程图

##### 2.2.2 视觉特征提取方法

可直接写作思路：

视觉特征提取是视频检索系统的核心步骤之一。随着视觉预训练模型的发展，基于 Vision Transformer 和 CLIP 风格模型的视觉编码方法在视频检索中表现出较强的迁移能力。当前项目使用 `ViT-H-14 / laion2b_s32b_b79k` 作为 baseline 特征提取模型，并进一步引入 `ViCLIP` 作为 teacher 表示来源，用于后续轻量蒸馏和候选重排序增强。

建议插图：

- 图2-5 视频视觉特征提取示意图
  内容建议：视频帧采样 -> 编码器 -> 特征向量

建议引用：

- ViT
- CLIP / OpenCLIP
- ViCLIP

##### 2.2.3 时序聚合方法

可直接写作思路：

视频由连续帧组成，如何将帧级或片段级特征聚合为更稳定的视频表示，是视频检索性能的重要影响因素。常见聚合方式包括平均池化、最大池化和更复杂的时序建模方法。当前系统主要采用平均池化与最大聚合作为可控、轻量的时序处理方式，并通过实验对其性能进行比较。

建议插图：

- 图2-6 时序聚合方式对比图

#### 2.3 向量检索与索引技术

##### 2.3.1 向量相似度计算方法

可直接写作思路：

在多模态检索系统中，文本查询和视频表示通常都会被映射到向量空间中，随后使用余弦相似度或内积相似度进行匹配。当前项目在归一化特征向量基础上采用内积相似度进行高效检索，与余弦相似度在单位向量场景下具有等价解释。

##### 2.3.2 FAISS 检索机制

可直接写作思路：

FAISS 是一种常用的大规模向量检索库，能够支持高效的近似或精确相似度搜索。当前系统使用 FAISS Flat Inner Product 索引构建 baseline 检索能力，其优点是实现直接、结果稳定，适合作为实验比较基准。在后续扩展中，也可以根据规模和延迟需求进一步考虑更复杂的近似索引结构。

建议插图：

- 图2-7 FAISS 检索流程图

建议引用：

- FAISS 官方论文

##### 2.3.3 Top-K 召回与视频级聚合策略

可直接写作思路：

在视频检索中，系统往往先通过向量索引召回 Top-K 片段候选，再将片段级得分聚合为视频级结果。Top-K 的选择直接影响后续重排序与 teacher 监督空间：如果 K 过小，可能错过正确视频；如果 K 过大，则会增加计算成本。当前项目通过全量 `1kA` candidate recall curve 分析了 `k=1,5,10,20,30,40,50` 的收益变化，最终将 `k=30` 作为当前轻量优化阶段的主要候选规模。

建议插图：

- 图2-8 Top-K 候选召回曲线图
  直接使用当前已经生成的曲线图

#### 2.4 大语言模型辅助检索相关技术

##### 2.4.1 查询改写的基本思想

可直接写作思路：

查询改写的核心思想是利用语义更丰富的表达替换或扩展原始查询，以提高检索系统与视频内容之间的匹配程度。在视频检索场景中，用户输入的自然语言通常较短且表达不完整，查询改写可以补充动作、场景、对象等语义信息，从而改善召回效果。

##### 2.4.2 歧义检测与选择性调用机制

可直接写作思路：

并非所有查询都需要改写，因此有必要先判断查询是否存在较强歧义或信息不足。歧义检测模块的作用在于估计当前查询是否适合进入 LLM 改写流程，从而避免不必要的调用成本。当前系统的设计思想也是“选择性调用”而不是“全量调用”。

##### 2.4.3 检索结果重排序机制

可直接写作思路：

重排序模块位于向量粗召回之后，用于对候选结果进行更细致的语义判断。其本质是让更强的语义模型重新评估候选视频与查询之间的匹配程度，从而改善最终排序质量。当前项目不仅有基于 LLM 的 rerank 设计，也引入了 `ViCLIP teacher` 与候选集内 listwise 学习的思路。

##### 2.4.4 缓存与成本控制策略

可直接写作思路：

为了保证系统具有工程可行性，LLM 与 teacher 模块必须配合缓存与调用控制策略使用。例如，teacher 侧仅保留 top-k soft labels、hard negatives 与必要的中间结果，避免保存过大的重复特征；对长任务引入进度显示和阶段性 checkpoint，有助于提升可维护性与可追踪性。

建议插图：

- 图2-9 LLM 辅助检索模块图
- 图2-10 缓存与成本控制示意图

建议引用：

- 查询改写与 rerank 代表文献
- LLM 增强检索与成本控制相关工作

#### 2.5 本章小结

写作要点：

- 总结第 2 章介绍的任务定义、特征表示、向量检索与 LLM 辅助检索技术
- 强调这些技术共同构成了第 3 章方法设计的理论基础

---

### 第3章 基于自然语言查询的视频检索方法

说明：

- 本章是论文核心
- 建议把“当前已实现并验证的 baseline / rewrite / rerank”写实
- 把“ViCLIP teacher + Stage 1-3”写成当前扩展优化路线，并明确哪些已做、哪些待做

#### 3.1 视频检索任务建模

##### 3.1.1 文本到视频检索任务定义

可直接写作思路：

本文研究的任务为文本到视频检索，即对于任意给定自然语言查询 `q`，在视频集合 `V={v1,v2,...,vn}` 中找出最符合该查询语义的视频，并输出按相关性排序的候选结果。为了实现这一目标，需要分别构建文本表示函数和视频表示函数，并定义统一的相似度函数用于跨模态匹配。

建议公式：

- 文本查询表示：
  `z_q = f_text(q)`
- 视频表示：
  `z_v = f_video(v)`
- 相似度函数：
  `s(q, v) = z_q^T z_v`

##### 3.1.2 视频片段表示与视频级表示

可直接写作思路：

考虑到视频序列通常较长，本文采用“片段级表示 + 视频级聚合”的方式建模视频内容。首先将每个视频切分为多个片段，并对每个片段提取视觉特征；随后根据片段特征构建视频级表示或视频级排序结果。该设计既便于大规模特征离线提取，也更适合结合 Top-K 召回与重排序流程。

建议插图：

- 图3-1 视频表示建模图

##### 3.1.3 视频检索目标与评价目标

可直接写作思路：

本文的检索目标是在保证系统计算成本可控的前提下，提高文本到视频检索的准确率，尤其重点提升 `Recall@1`。同时，为了保证方法具有工程可落地性，还需要兼顾 `Recall@5`、`Recall@10`、响应延迟以及缓存开销等因素。

#### 3.2 整体方法框架

##### 3.2.1 基线检索流程

可直接写作思路：

本文的 baseline 检索流程包括：视频预处理与片段划分、视觉特征提取、特征存储、FAISS 向量索引构建、文本查询编码、Top-K 片段召回以及视频级聚合排序。该流程构成整个系统的基础检索层，也是后续查询改写与重排序模块的运行前提。

建议插图：

- 图3-2 baseline 检索流程图
  内容建议：视频 -> 切分 -> 特征 -> 索引；文本 -> 编码 -> 检索 -> 聚合 -> 排序

##### 3.2.2 查询改写增强流程

可直接写作思路：

在 baseline 流程之上，本文设计了查询改写增强流程。系统首先对原始查询进行歧义检测，当判定其表达不足或语义模糊时，调用大语言模型进行改写或扩展，并将改写后的查询送入检索模块。该流程的目标是提升查询与视频内容之间的语义对齐程度。

建议插图：

- 图3-3 选择性查询改写流程图

##### 3.2.3 候选结果重排序流程

可直接写作思路：

在 baseline 或 rewrite 召回结果基础上，系统进一步对候选视频集合进行重排序。重排序模块通过更强的语义评分机制对候选结果进行再评估，从而将更符合查询细粒度语义的视频提升到更靠前的位置。当前系统已有基于 LLM 的 rerank 路线，并正在扩展 `ViCLIP teacher` + 轻量 student 学习路线。

建议插图：

- 图3-4 候选结果重排序流程图

#### 3.3 基线视频检索方法

##### 3.3.1 视频数据预处理与片段划分方法

可直接写作思路：

本文在 MSR-VTT 数据集上构建实验环境，并对原始视频进行统一预处理。考虑到视频长度和内容变化的差异，系统采用固定策略将视频切分为若干片段，以便于后续离线特征提取与索引构建。该方法具有实现简单、可扩展性强和适合大规模批处理的优点。

建议插图：

- 图3-5 视频预处理与片段划分示意图

##### 3.3.2 视频片段特征提取方法

可直接写作思路：

在视频片段特征提取阶段，本文使用预训练视觉模型 `ViT-H-14 / laion2b_s32b_b79k` 对采样帧进行编码，并通过时序聚合得到片段级表示。随后将所有片段特征离线保存，用于索引构建和后续检索。该阶段是系统中最重要的离线计算部分。

建议插图：

- 图3-6 视频特征提取模块图

建议引用：

- OpenCLIP / ViT-H

##### 3.3.3 向量索引构建与召回方法

可直接写作思路：

系统将提取得到的片段特征组织为向量集合，并使用 FAISS 构建基于内积相似度的向量索引。在检索阶段，系统先对输入查询进行文本编码，再在 FAISS 索引中进行 Top-K 片段搜索，得到初始候选结果。该阶段承担高效粗召回的作用。

建议插图：

- 图3-7 FAISS 向量索引与召回示意图

##### 3.3.4 视频级结果聚合方法

可直接写作思路：

由于同一视频可能包含多个片段，片段检索结果需要进一步转化为视频级结果。本文采用片段到视频的聚合策略，将同一视频下多个片段的相似度结果汇总为视频得分，并按得分降序排列生成最终视频检索结果。当前系统采用的主要策略是基于最大值的聚合方法。

建议插图：

- 图3-8 视频级结果聚合图

#### 3.4 选择性查询改写方法

##### 3.4.1 查询歧义评分方法

可直接写作思路：

为了避免对所有查询无差别调用大语言模型，本文首先对用户输入查询进行歧义评分。评分依据可以包括查询长度、语义完整度、实体与动作信息是否充分、是否存在明显省略或多义表达等。系统根据该评分决定是否进入查询改写流程。

建议插图：

- 图3-9 查询歧义评分流程图

##### 3.4.2 查询改写生成方法

可直接写作思路：

当查询被判定为需要改写时，系统调用大语言模型对其进行语义增强，生成更完整、更适合检索的改写查询。改写可以包括补充动作、场景、对象、关系等关键信息，也可以对原始表达进行规范化。为了控制噪声，本文采用选择性调用策略，并通过实验对不同改写策略进行比较。

建议插图：

- 图3-10 查询改写示例图
  内容建议：原始查询、改写查询、检索结果变化示意

建议引用：

- 查询改写相关文献
- LLM 在信息检索中的改写应用文献

#### 3.5 基于大语言模型的候选结果重排序方法

##### 3.5.1 候选视频筛选方法

可直接写作思路：

由于对全部视频进行高成本语义评分不现实，本文首先在 baseline 召回结果中选取 Top-K 候选视频作为重排序对象。当前实验进一步通过 candidate recall curve 分析了不同 K 值的收益变化，发现 `k=30` 能够在精度空间与计算开销之间提供较好的平衡，因此在轻量优化阶段采用 `topk=30` 的候选集。

建议插图：

- 图3-11 Top-K 候选筛选示意图
- 图3-12 Candidate Recall Curve
  可直接引用当前已生成曲线图

##### 3.5.2 候选视频语义评分方法

可直接写作思路：

在候选视频筛选之后，系统需要对候选集合进行更细粒度的语义评分。当前已有两条思路：其一是基于大语言模型的语义打分与重排序；其二是基于 `ViCLIP` teacher 对 baseline 候选进行重打分，并进一步通过轻量 adapter 或 listwise distillation 学习更优排序偏好。当前项目已经完成真实 `ViCLIP` teacher 接入，并在轻量 Stage 1 中进行了初步验证。

建议插图：

- 图3-13 候选语义评分流程图
  内容建议：baseline 候选 -> teacher / LLM 评分 -> rerank / student 学习

建议引用：

- ViCLIP
- Ranking Distillation
- ColBERT / late interaction

##### 3.5.3 候选结果重排序方法

可直接写作思路：

候选语义评分完成后，系统按照新的评分结果重新对候选视频进行排序，从而得到最终输出。对于当前系统而言，重排序既可以是直接在线 rerank，也可以是离线 teacher 监督 + 在线轻量 student 的方式。在论文中应明确说明：当前 baseline、rewrite 和 rerank 已形成完整可运行系统，而 teacher-guided 路线属于当前正在推进的增强方向。

建议插图：

- 图3-14 重排序前后结果示意图

#### 3.6 实验方案设计

##### 3.6.1 Baseline 实验方案

可直接写作思路：

Baseline 实验主要用于验证基础视频检索流程的有效性，包括特征提取、索引构建、查询编码、Top-K 召回和视频级聚合。实验中应说明所采用的数据集、划分方式、参数设置以及评价指标，并给出当前 baseline 的主要结果。

建议插图：

- 图3-15 baseline 实验流程图

##### 3.6.2 Rewrite 消融实验方案

可直接写作思路：

Rewrite 消融实验用于分析查询改写模块对检索效果的影响。实验应比较原始查询、全量改写、选择性改写等不同策略，并分析改写对不同类型查询的帮助程度，以及改写引入的额外开销。

建议插图：

- 图3-16 rewrite 消融实验设计图

##### 3.6.3 Rerank 消融实验方案

可直接写作思路：

Rerank 消融实验用于分析候选结果重排序模块的效果，重点比较 baseline、rewrite+baseline、rerank 以及 teacher-guided 轻量增强等多种方案。对于当前项目，应明确写出 `1kA 200-query` 作为快速验证协议，全量 `1kA` 作为后续提升通过后的正式验证协议。

建议插图：

- 图3-17 rerank / teacher-guided 消融实验设计图

#### 第3章可加入的图表总表

- 图3-1 任务建模图
- 图3-2 baseline 检索流程图
- 图3-3 查询改写流程图
- 图3-4 候选重排序流程图
- 图3-5 视频预处理与切分图
- 图3-6 视频特征提取图
- 图3-7 FAISS 索引构建与召回图
- 图3-8 视频级聚合图
- 图3-9 查询歧义评分图
- 图3-10 查询改写示例图
- 图3-11 Top-K 候选筛选图
- 图3-12 Candidate Recall Curve
- 图3-13 候选语义评分图
- 图3-14 重排序前后结果对比图
- 图3-15 Baseline 实验流程图
- 图3-16 Rewrite 消融实验图
- 图3-17 Rerank / Teacher-guided 消融实验图

#### 第一到第三章建议重点引用文献类型

- 视频检索综述
- 多模态检索综述
- CLIP / OpenCLIP / ViT 相关论文
- VideoCLIP / X-CLIP / ViCLIP 相关论文
- FAISS 官方论文
- Ranking Distillation / listwise distillation 相关论文
- ColBERT / late interaction 相关论文
- LLM 查询改写、LLM rerank、LLM for IR 相关论文
- MSR-VTT 数据集与 benchmark 论文

#### 写作注意事项

- 对当前还未完成最终提升的 teacher-guided 路线，要写成：
  “本文进一步探索了……”
  “当前实验表明……”
  “后续将继续从……方向优化……”
- 不要把尚未取得稳定提升的 Stage 2 / Stage 3 写成最终结论
- 第一章重在问题提出与研究意义
- 第二章重在理论铺垫与关键技术梳理
- 第三章重在方法流程、系统设计思路与实验方案组织
