# 项目阶段性状态文档（中文接手版）

## 1. 这份文档的用途

- 这份文档用于“无记忆接手”当前项目
- 目标不是完整介绍所有历史，而是让下一次接手时能在几分钟内知道：
  当前项目做到哪里了
  哪些结果已经验证
  哪些文件最关键
  下一步该从哪开始

## 2. 项目当前主目标

- 当前主目标：
  在 `MSRVTT 1kA` 协议上，把 `ViT-H-14 / laion2b_s32b_b79k` baseline 从
  `R@1 ≈ 47` 往 `60` 推
- 当前执行策略：
  优先走轻量路线，不直接上重型多 teacher 全量蒸馏
- 当前快速验收标准：
  每轮 student 更新先跑 `1kA 200-query`
  只有当 `R@1 > 48` 且 `R@5/R@10` 有明显提升时，才值得继续推进到 full
  `1kA`

## 3. 当前已确认的关键事实

### 3.1 数据与索引状态

- `data/raw_videos/msrvtt` 已切换到完整 `10000` 视频版本
- `msrvtt_fixed.jsonl` 已重建为 Linux 可用路径
- full `msrvtt_fixed` `ViT-H` features 已抽取完成
- full `msrvtt_fixed` FAISS index 已建立完成
- `msrvtt_fixed_1kA` 的评测索引也存在并可正常使用

### 3.2 baseline 状态

- 当前可信 baseline：
  `R@1 47.0 / R@5 65.0 / R@10 72.0`
- 对应产物：
  [baseline_vith14_mean_topk200_max_N200_recheck.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_mean_topk200_max_N200_recheck.json)
- 这个 baseline 已在当前环境复核通过，可以作为后续实验比较基准

### 3.3 teacher 状态

- 真正的 `ViCLIP` 已接通，不再只是计划名义
- 关键实现文件：
  [viclip_encoder.py](E:/BISHE/video_retrieval_system/src/features/viclip_encoder.py)
  [build_viclip_teacher_supervision.py](E:/BISHE/video_retrieval_system/scripts/build_viclip_teacher_supervision.py)
- 当前 teacher 路径：
  先用 baseline 召回候选，再用 `ViCLIP` 对候选做重打分，生成紧凑 supervision

## 4. 当前推荐继续看的文件顺序

如果下次要快速恢复上下文，优先看下面这些：

1. [project_status_handoff_zh.md](E:/BISHE/video_retrieval_system/docs/project_status_handoff_zh.md)
   先看这份
2. [technical_stage_notes.md](E:/BISHE/video_retrieval_system/docs/technical_stage_notes.md)
   看实验结果和关键判断
3. [remote_training_runbook.md](E:/BISHE/video_retrieval_system/docs/remote_training_runbook.md)
   看当前推荐执行顺序
4. [todo.md](E:/BISHE/video_retrieval_system/todo.md)
   看更完整的项目与论文说明
5. [run_stage1_light_pipeline.py](E:/BISHE/video_retrieval_system/scripts/run_stage1_light_pipeline.py)
   看当前轻量 Stage 1 自动流程
6. [run_stage_experiment.py](E:/BISHE/video_retrieval_system/scripts/run_stage_experiment.py)
   看 student 训练与 quick eval 如何串起来
7. [text_adapter.py](E:/BISHE/video_retrieval_system/src/learning/text_adapter.py)
   看当前 student 实现细节

## 5. 当前目录结构的重点理解

### 5.1 `data/`

- `data/raw_videos/`
  原始视频
- `data/features/`
  baseline 视频特征
- `data/indexes/`
  FAISS 索引
- `data/cache/viclip/video_features/`
  `ViCLIP` teacher 视频侧缓存

### 5.2 `outputs/`

- `outputs/tables/analysis/`
  绝大多数实验 summary、candidate recall、teacher 文件、gate 文件都在这里
- `outputs/feedback/learning_diary.jsonl`
  学习记录日志
- `outputs/figures/`
  曲线图等图片产物

### 5.3 `scripts/`

- `extract_features.py`
  抽 full feature
- `build_index.py`
  建 full index
- `eval_msrvtt.py`
  baseline 评测
- `eval_candidate_recall.py`
  单个 `k` 的候选召回
- `eval_candidate_recall_sweep.py`
  `k` 曲线 sweep + 画图
- `build_viclip_teacher_supervision.py`
  构建 `ViCLIP` teacher
- `run_stage_experiment.py`
  训练 student 并做 quick eval
- `run_stage1_light_pipeline.py`
  轻量 Stage 1 自动流水线
- `check_acceptance_gate.py`
  quick/full gate 判断

### 5.4 `src/`

- `src/features/`
  特征编码
- `src/retrieval/`
  搜索与索引
- `src/evaluation/`
  评测逻辑
- `src/learning/`
  teacher supervision 与 text adapter
- `src/llm/`
  rewrite、memory、policy、rerank 相关逻辑

## 6. 当前已经做过的主要实验

### 6.1 baseline 复核

- 已完成
- 结果稳定：
  `47 / 65 / 72`

### 6.2 bootstrap teacher quick run

- 已做
- 失败
- 结论：
  bootstrap `ViT-H` retrieval teacher 不适合作为主 Stage 1 路线

### 6.3 `ViCLIP` q200 teacher 构建

- 已做
- 成功
- 说明真实 `ViCLIP` 接入链路正常

### 6.4 candidate recall 单点评估

- 已做
- `topk30` 全量 `1kA` 候选召回：
  `R@30 = 83.78`

### 6.5 candidate recall 曲线 sweep

- 已做
- `k = 1, 5, 10, 20, 30, 40, 50`
- 结果：
  `39.00 / 61.86 / 71.24 / 79.98 / 83.78 / 86.36 / 88.30`
- 结论：
  当前 `k=30` 是较合理折中点
- 对应产物：
  [baseline_vith14_candidate_recall_curve_1kA_full.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_candidate_recall_curve_1kA_full.json)
  [baseline_vith14_candidate_recall_curve_1kA_full.png](E:/BISHE/video_retrieval_system/outputs/figures/baseline_vith14_candidate_recall_curve_1kA_full.png)

### 6.6 轻量 Stage 1：Top-k30 + ViCLIP teacher

- 已做第一轮
- 配置：
  `student_topk=30`
  `teacher_topk=10`
  `max_train_queries=2000`
  `max_eval_queries=200`
- 结果：
  baseline 仍最好
- 失败原因判断：
  当前 text adapter 更新过于激进，破坏了 baseline 排序结构

### 6.7 轻量 Stage 1：Tuned V1

- 已做第二轮
- 调低了 teacher loss 权重
- 关闭了 late interaction
- 使用更保守 fusion
- 结果：
  更稳，但仍未超过 baseline
- 结论：
  只靠当前 adapter 权重调参，不足以实现明显提升

## 7. 当前最重要的判断

### 7.1 当前最可信的路线

- 不是“全量重蒸馏”
- 而是：
  baseline candidate recall 分析
  -> 选合适 `k`
  -> 在候选集内做轻量 teacher supervision
  -> 用 quick gate 控制实验推进

### 7.2 当前最主要的问题

- 问题不在 `ViCLIP` 是否可用
- 也不在数据、索引、baseline 是否正确
- 当前主要问题是：
  现有 `text adapter` student 更新方式会破坏 baseline 排序稳定性

### 7.3 当前不建议直接做的事

- 不建议直接推进重型 Stage 2 / Stage 3
- 不建议直接做全量高成本 frame teacher / late interaction teacher
- 不建议在没有 Stage 1 快速胜利前就把系统复杂度继续抬高

## 8. 当前最值得继续做的事

### 8.1 优先事项

- 继续保留 `k=30`
- 重新设计更保守的 Stage 1 student 更新方式
- 比如：
  更小 residual scale
  gated residual
  更偏 fusion/listwise 的轻量学习
  硬样本子集训练
  只对“baseline rank 在 2~30 内”的查询增强

### 8.2 完成标准

- 先过 `1kA 200-query`
- 要求：
  `R@1 > 48`
  且 `R@5 / R@10` 明显提升
- 只有过了这个门，再考虑 full `1kA`

## 9. 当前最关键的产物文件

### 必看结果文件

- [baseline_vith14_mean_topk200_max_N200_recheck.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_mean_topk200_max_N200_recheck.json)
- [baseline_vith14_candidate_recall_top30_1kA_full.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_candidate_recall_top30_1kA_full.json)
- [baseline_vith14_candidate_recall_curve_1kA_full.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/baseline_vith14_candidate_recall_curve_1kA_full.json)
- [stage1_viclip_topk30_q2000_quick200.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/stage1_viclip_topk30_q2000_quick200.json)
- [stage1_viclip_topk30_q2000_quick200_tuned_v1.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/stage1_viclip_topk30_q2000_quick200_tuned_v1.json)
- [stage1_viclip_topk30_q2000_gate.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/stage1_viclip_topk30_q2000_gate.json)
- [stage1_viclip_topk30_q2000_quick200_tuned_v1_gate.json](E:/BISHE/video_retrieval_system/outputs/tables/analysis/stage1_viclip_topk30_q2000_quick200_tuned_v1_gate.json)

### 必看 teacher 文件

- [viclip_teacher_supervision_q200.jsonl](E:/BISHE/video_retrieval_system/outputs/tables/analysis/viclip_teacher_supervision_q200.jsonl)
- [viclip_teacher_supervision_stage1_topk30_q2000.jsonl](E:/BISHE/video_retrieval_system/outputs/tables/analysis/viclip_teacher_supervision_stage1_topk30_q2000.jsonl)

## 10. 关于 `learning_diary.jsonl` 的提醒

- 这个文件里混有当前阶段日志和更早的旧日志/其他路线日志
- 其中有些条目和当前主线并不完全一致
- 因此：
  `learning_diary.jsonl` 可作为参考，但不能单独作为唯一事实来源
- 真正接手时，应优先以：
  `technical_stage_notes.md`
  `project_status_handoff_zh.md`
  `outputs/tables/analysis/` 中的现有结果文件
  为准

## 11. 一句话接手指令

如果下次没有上下文，建议直接从这句话开始：

> 当前项目已经完成 full 数据、feature、index、baseline 复核和真实 ViCLIP teacher 接入；当前可信 baseline 为 `47/65/72`；candidate recall 曲线已表明 `k=30` 是当前轻量路线的合理折中；已做两轮 `topk30 + ViCLIP teacher + Query200` 的轻量 Stage 1，但都未超过 baseline；下一步应继续做更保守的 student 更新设计，而不是直接推进重型 Stage 2/3。

## 12. 下次建议直接执行的命令

### 看 baseline

```bash
python -u scripts/eval_msrvtt.py \
  --manifest msrvtt_fixed_1kA.jsonl \
  --queries msrvtt_1kA_test_queries.jsonl \
  --pooling mean \
  --model_name ViT-H-14 \
  --pretrained laion2b_s32b_b79k \
  --topk 200 \
  --max_queries 200 \
  --out outputs/tables/analysis/baseline_vith14_mean_topk200_max_N200_recheck.json
```

### 看 candidate recall 曲线

```bash
python -u scripts/eval_candidate_recall_sweep.py \
  --manifest msrvtt_fixed_1kA.jsonl \
  --queries msrvtt_1kA_test_queries.jsonl \
  --pooling mean \
  --model_name ViT-H-14 \
  --pretrained laion2b_s32b_b79k \
  --cutoffs 1,5,10,20,30,40,50 \
  --out_json outputs/tables/analysis/baseline_vith14_candidate_recall_curve_1kA_full.json \
  --out_png outputs/figures/baseline_vith14_candidate_recall_curve_1kA_full.png
```

### 跑当前轻量 Stage 1 自动链路

```bash
python -u scripts/run_stage1_light_pipeline.py \
  --student_topk 30 \
  --teacher_topk 10 \
  --max_train_queries 2000 \
  --max_eval_queries 200
```

## 13. 当前结论

- 项目基础设施已经搭好
- 当前主线不是数据准备问题，也不是 teacher 接不通问题
- 当前瓶颈是：
  如何在不破坏 baseline 的前提下，把 teacher 信号轻量地转化为真正的
  `R@1/R@5/R@10` 提升
