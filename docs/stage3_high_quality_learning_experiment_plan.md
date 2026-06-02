# Stage 3 高质量样本扩展实验计划

## 实验目标

本轮实验不再把 `max_train_queries` 的扩大本身视为增益来源，而是把“有效高质量学习样本数”作为独立实验因素。目标是在不泄露 locked 1kA 测试信息的前提下，从 safe_train 中扩大候选范围，并通过 teacher rank、uncertainty、alignment overlap 等指标筛选出约 500 条可用于学习的高质量样本。

## 当前诊断结论

| 诊断名称 | teacher supervision | 候选 query 数 | 通过筛选数 | 是否达到 500 | 主要结论 |
|---|---|---:|---:|---|---|
| `diagnose_highquality_pool_q500_rank12_target500_v1` | `viclip_teacher_supervision_stage2_safe_train_q500_cov100_t20_v1.jsonl` | 500 | 222 | 否 | 当前最优 v3.5 实际只使用 222 条有效样本，样本质量较高但数量不足。 |
| `diagnose_highquality_pool_q800_rank12_target500_v1` | `viclip_teacher_supervision_stage2_safe_train_q800_gpu_v1.jsonl` | 800 | 0 | 否 | q800 文件缺少强制 GT 覆盖，不适合作为高质量筛选学习来源。 |

因此，下一步应生成“带 GT 强制保留和更大候选覆盖”的 teacher supervision，而不是直接复用旧 q800。

当前工具已支持把通过筛选的样本导出为独立 query 子集和 teacher 子集。例如 q500 诊断会生成：

- `outputs/tables/analysis/queries_subset_highquality222_from_q500_rank12_v1.jsonl`
- `outputs/tables/analysis/teacher_subset_highquality222_from_q500_rank12_v1.jsonl`

后续 q1500/q2000 达到 500 条有效样本后，也应导出 `highquality500` 子集，再只基于该子集训练 student。

## 新增实验因素

| 因素名称 | 控制变量 | 对照目的 |
|---|---|---|
| 有效高质量样本数 | 222 / 约 500 | 判断性能提升来自样本质量与数量，而不是单纯扩大 q。 |
| Alignment teacher | off / on | 判断局部动作、对象、关系监督是否是主增益来源。 |
| Multiview features | off / on | 判断多视角视频表示是否提升 top1 校准。 |
| Pairwise hard negative | off / on | 判断相似候选间的排序边界是否得到改善。 |
| Query-aware fusion | off / on | 后续可选，用于判断不同 query 类型是否需要动态使用不同视频视角。 |
| Error-type pairwise ranking | off / on | 判断 GT-vs-hard-negative 的强排序约束是否比温和 listwise 蒸馏更有效。 |
| Component-to-view alignment | off / on | 判断 query component 与 early/middle/late 视频视角的显式局部匹配是否能释放 multiview 特征增益。 |
| Fine temporal view tokens | 3 / 6 | 判断视频侧从 coarse early/middle/late 细化为 6 个 temporal tokens 后，是否能增强局部证据匹配。 |

## 建议实验命名

| 实验名 | 含义 |
|---|---|
| `stage3_align_multiview_q500_effective222_eval1kAq200_v1` | 当前最好 q200 方法的清晰命名版本，强调 q500 候选中实际有效样本为 222。 |
| `stage3_highquality500_teacher_q2000_diagnosis_v1` | 只做样本池诊断，不训练，用于确认是否达到 500 条有效样本。 |
| `stage3_highquality500_align_multiview_q2000_eval1kAq200_v1` | 约 500 条高质量样本 + alignment + multiview 的主实验。 |
| `stage3_highquality500_align_only_q2000_eval1kAq200_v1` | 只开 alignment teacher，用于拆分贡献。 |
| `stage3_highquality500_multiview_only_q2000_eval1kAq200_v1` | 只开 multiview features，用于拆分贡献。 |
| `stage3_highquality500_align_multiview_pairwise_q2000_eval1kAq200_v1` | 在主实验上加入 pairwise hard negative，判断边界学习是否有效。 |
| `stage3_highquality500_align_multiview_pairwise_queryaware_q2000_eval1kAq200_v1` | 加入 query-aware fusion，使 action/relation/person_attribute 类型查询更依赖局部对齐与多视角证据。 |
| `stage3_highquality500_componentview_align_multiview_pairwise_queryaware_q2000_eval1kAq200_v1` | 加入 component-to-view alignment，将 action/object/scene/relation 组件文本与 early/middle/late 视频视角显式匹配。 |
| `stage3_highquality500_componentview_vtokens6_align_multiview_pairwise_queryaware_q2000_eval1kAq200_v1` | 将视频侧 multiview 从 3 个粗视角扩展为 6 个 temporal view tokens，再做 component-to-view alignment。 |

## 推荐执行顺序

1. 生成更大范围 teacher supervision，并强制保留 GT。
2. 用诊断脚本检查有效样本是否达到 500。
3. 若不足 500，优先扩大 safe_train 候选范围；其次轻微放宽 `max_teacher_rank`，不要直接放宽 uncertainty 到无约束。
4. 达到 500 后再跑训练，避免长时间训练低价值样本池。
5. 先在 1kA q200 做快速对照；确认有效后，再跑完整 locked 1kA。

## 评价口径

本轮报告中必须同时写出：

- `max_train_queries`：候选训练 query 数。
- `accepted_before_topk`：筛选前通过 gate 的有效样本数。
- `selected_after_topk`：最终进入训练的有效样本数。
- `accepted_gt_rank_mean`：teacher 中 GT 平均排名。
- `accepted_uncertainty_mean`：teacher 置信质量。
- `accepted_alignment_overlap_mean`：alignment teacher 对局部语义覆盖程度。
- locked 1kA q200 或 full 1kA 的 R@1 / R@5 / R@10。

只有当有效样本数、质量指标和 locked recall 同时改善时，才能说明“扩大高质量学习样本”是有效因素。
