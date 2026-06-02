# 第三章与摘要补全稿：外部性能对比、算法消融与摘要重写

> 使用位置建议：本文件内容用于补充 `docs/19220717赵月论文初稿.docx`。建议优先替换摘要，并在第3章 `3.6 联合训练目标与方法消融设计` 后新增“近年方法性能对比与本文方法分析”相关内容。文中表号可按最终 Word 排版顺序调整。

## 一、摘要替换稿

### 摘 要

随着在线视频规模持续扩大，用户越来越倾向于直接使用自然语言描述检索目标视频。现有文本到视频检索方法多依赖视觉语言预训练模型，将文本和视频映射到统一语义空间，并通过向量相似度完成候选召回。这类方法具有较高效率，但在复杂查询下仍存在首位排序不稳定的问题：当多个候选视频在场景、主体或动作上整体相近时，模型往往能够召回相关视频，却难以准确判断哪一个视频真正满足查询中的局部动作、对象关系和人物属性约束。

针对上述问题，本文设计了一种面向自然语言视频检索的细粒度表征增强方法，并在此基础上实现了完整检索系统。系统以 MSR-VTT 数据集为实验对象，使用预训练视觉语言模型提取文本与视频特征，通过 FAISS 构建向量索引完成基础召回；同时设置选择性查询改写和候选重排序模块，用于分析大语言模型在查询补充和候选语义校准中的辅助价值。实验表明，这类系统型增强可以改善部分查询，但整体收益受查询清晰度、候选质量和调用成本限制，难以单独解决相似候选内部的细粒度排序问题。

本文的核心改进是提出查询感知多视角对齐与错误驱动成对教师监督方法。该方法利用 alignment teacher 引导学生模型关注查询中的动作、对象、关系和人物属性等语义成分，并通过 multiview features 为视频侧补充多帧、多时间窗的局部证据；进一步地，本文将 near-failure 样本构造成成对排序监督，使模型学习正确视频与相似错误候选之间的判别边界。在 locked 1kA 正式协议下，本文 方法的 R@1 达到 39.7%，相较前一阶段细粒度增强结果 38.7% 提升 1.0 个百分点；纯 student adapter 的 R@5 和 R@10 分别达到 61.6% 和 72.1%，说明该方法不仅改善首位排序，也提升了候选列表的整体排序质量。

此外，本文实现了前端检索、历史记录、学习日志、消融结果展示和错误反馈记录等系统功能，并对错误驱动自学习闭环进行了初步探索。实验结果表明，反馈学习在部分验证设置上具有局部正向效果。总体来看，本文工作完成了从数据处理、基础召回、细粒度表征增强到系统展示的完整实现路径，并验证了局部对齐教师、多视角视频证据和错误驱动排序监督在自然语言视频检索中的有效性。

关键词：文本到视频检索；自然语言查询；跨模态检索；细粒度对齐；多视角特征；成对教师监督

### Abstract

With the rapid growth of online videos, users increasingly expect to retrieve target videos through natural-language descriptions. Existing text-to-video retrieval methods usually rely on pretrained vision-language models, which project textual queries and videos into a shared semantic space and retrieve candidates by vector similarity. This paradigm is efficient, but it remains limited for complex queries. When several candidate videos are similar in scenes, subjects, or actions, the model may retrieve relevant videos but fail to rank the truly matching one at the top.

To address this issue, this thesis proposes a fine-grained representation enhancement method for natural-language video retrieval and implements a complete retrieval system based on it. The system is evaluated on the MSR-VTT dataset. It extracts text and video features with a pretrained vision-language model and builds a FAISS index for efficient candidate retrieval. Selective query rewriting and candidate reranking are also implemented to examine the auxiliary role of large language models in query enrichment and semantic calibration. The experiments show that these pipeline-level modules are useful for certain queries, but their overall gains are constrained by query clarity, candidate quality, and inference cost.

The main contribution of this thesis is a query-aware multiview alignment method with error-driven pairwise teacher supervision. The alignment teacher encourages the student model to focus on semantic components such as actions, objects, relations, and person attributes, while multiview features provide additional local video evidence from multiple frames and temporal windows. Furthermore, near-failure cases are converted into pairwise ranking supervision, so that the student model can learn the boundary between the ground-truth video and highly similar negative candidates. Under the locked 1kA evaluation protocol, the proposed Stage4 method reaches 39.7% R@1, improving the previous fine-grained enhancement result by 1.0 percentage point. The pure student adapter achieves 61.6% R@5 and 72.1% R@10, indicating that the proposed method improves not only first-rank calibration but also the overall candidate ranking quality.

In addition, this thesis implements front-end retrieval, search history, learning logs, ablation visualization, and feedback recording. An error-driven self-learning loop is also explored. Although this loop shows local positive effects under some validation settings, it has not yet consistently surpassed the current best model on locked 1kA. Overall, this work provides a complete implementation path from data processing and baseline retrieval to fine-grained representation enhancement and system demonstration, and verifies the effectiveness of local alignment supervision, multiview video evidence, and error-driven pairwise ranking in natural-language video retrieval.

Keywords: text-to-video retrieval; natural-language query; cross-modal retrieval; fine-grained alignment; multiview features; pairwise teacher supervision

## 二、第三章新增小节建议

建议在 `3.6.5 核心表征增强消融` 之后，新增如下小节：

```text
3.6.6 近年方法性能对比与本文方法定位
3.6.7 本文算法消融实验汇总
```

其中，`3.6.6` 回应老师提出的“算法需要和近年方法做性能对比”；`3.6.7` 回应“消融不仅要有图，也要有表”的要求。这样第3章既有算法描述，也有能支撑算法有效性的表格证据。

## 三、3.6.6 近年方法性能对比与本文方法定位

近年来，MSR-VTT 1kA 已成为文本到视频检索任务中使用较多的公开协议之一。为了说明本文方法在相关研究中的位置，本文选取了 CLIP4Clip、X-Pool、X-CoT、BT-Adapter、ViCLIP 等具有代表性的近年方法进行对比。需要说明的是，不同公开方法在骨干网络、预训练数据规模、训练方式和是否使用额外推理模块等方面存在差异，因此该表主要用于展示本文方法的性能区间和方法特点，而不将其简单解释为完全同条件下的逐项竞赛。

**表 3-X  MSR-VTT 1kA 文本到视频检索公开方法对比**

| 方法 | 年份 | 方法特点 | R@1 | R@5 | R@10 | 结果来源与说明 |
|---|---:|---|---:|---:|---:|---|
| CLIP | 2021 | 图文预训练模型直接迁移 | 31.6 | 53.8 | 63.4 | X-CoT 论文汇总结果 |
| X-CoT | 2025 | LLM CoT 推理增强检索 | 37.2 | 61.8 | 71.5 | X-CoT 单独方法结果 |
| How2Cap | 2024 | 视频文本生成与检索结合 | 37.6 | 62.0 | 73.3 | X-CoT 论文汇总结果 |
| TVTSv2 | 2023 | 视频文本预训练方法 | 38.2 | 62.4 | 73.2 | X-CoT 论文汇总结果 |
|                  |      |                                        |      |      |      |                       |
|                  |      |                                        |      |      |      |                       |
| 本文 Stage4 增强 | 2026 | adapter + alignment/multiview 系统增强 | 39.7 | 61.3 | 71.6 | 本文当前 R@1 最优结果 |
| BT-Adapter | 2024 | 参数高效视频迁移 | 40.9 | 64.7 | 73.5 | CVPR 2024 论文结果 |
| ViCLIP | 2024 | 大规模视频语言预训练 | 42.4 | - | - | X-CoT 论文汇总结果 |
| CLIP4Clip | 2021 | CLIP 视频检索经典强基线 | 44.5 | 71.4 | 81.6 | CLIP4Clip 公开结果 |
| X-Pool | 2022 | 查询感知视频帧聚合 | 46.9 | 73.0 | 82.0 | X-CoT 论文汇总结果 |
| X-CoT + X-Pool | 2025 | CoT 推理结合 X-Pool | 47.3 | 73.3 | 82.1 | X-CoT 论文结果 |

从表 3-X 可以看出，本文 Stage4 方法相较 CLIP 直接迁移、X-CoT 单独增强、How2Cap 和 TVTSv2 等结果具有更高的 R@1。与 BT-Adapter、ViCLIP、CLIP4Clip 和 X-Pool 等更强公开方法相比，本文结果仍存在差距，主要原因在于这些方法通常采用更大规模的预训练、更完整的训练流程或更强的视频语言基础模型。本文没有直接复现这些大规模训练设置，而是在本地可运行的轻量双塔检索系统中，引入查询感知多视角融合和错误驱动成对教师监督，重点验证细粒度对齐增强对学生检索表示的改善作用。

因此，本文方法的优势不宜表述为“全面超过所有已有方法”，而应更准确地概括为：在保持高效向量检索和轻量 adapter 训练的前提下，本文方法能够吸收 X-Pool 的查询感知思想、X-CoT 的推理式监督思想以及 BT-Adapter 的参数高效迁移思想，并在 locked 1kA 正式协议下取得稳定增益。这说明细粒度对齐教师、多视角视频证据和错误驱动 pairwise teacher 的组合具有实际价值，也为后续接入更强视频侧特征或更大规模 teacher 提供了明确方向。

## 四、3.6.7 本文算法消融实验汇总

为了进一步验证本文各项改进的有效性，本文在受控条件下进行了多组消融实验。外部方法对比用于说明本文方法在公开研究中的位置，而消融实验则用于回答“本文哪些改进真正产生了作用”。因此，表 3-X 将 baseline、固定多视角融合、查询感知多视角融合、错误驱动 pairwise teacher 以及后续扩展方法放在同一框架下比较。

**表 3-X  本文细粒度增强方法消融结果**

| 实验编号 | 方法设置 | 评测协议 | R@1 | R@5 | R@10 | MnR | 主要结论 |
|---|---|---|---:|---:|---:|---:|---|
| E0 | 原始 baseline | q200 | 47.5 | 65.0 | 72.0 | 17.32 | 基础召回有效，但首位排序仍有提升空间 |
| E1 | alignment teacher + fixed multiview | q200 | 50.5 | 64.5 | 73.5 | 20.42 | 固定多视角融合明显提升 R@1 |
| E2 | query-aware multiview + pairwise teacher | q200 | 49.0 | 66.5 | 75.5 | 20.205 | R@5/R@10 提升较明显，Top-1 仍有波动 |
| E3 | E2 + alignment/multiview 增强评分 | q200 | 51.0 | 66.5 | 75.0 | 20.72 | 局部对齐证据进一步改善首位校准 |
| E4 | alignment teacher + fixed multiview | full 1kA | 38.7 | 61.1 | 70.9 | 29.112 | 上一阶段 full 1kA 最优结果 |
| E5 | query-aware multiview + pairwise teacher | full 1kA | 39.1 | 61.6 | 72.1 | 28.269 | 纯 student adapter 稳定提升 R@1/R@5/R@10 |
| E6 | E5 + alignment/multiview 增强评分 | full 1kA | 39.7 | 61.3 | 71.6 | 28.478 | 当前 full 1kA R@1 最优结果 |
| E7 | safe_dev 权重搜索后推理增强 | full 1kA | 39.5 | 61.9 | 72.5 | 27.741 | 对 R@5/R@10 和 MnR 更有利，但 R@1 略低于 E6 |
| E8 | BT-style temporal adapter | full 1kA | 39.1 | 61.9 | 72.1 | 28.016 | 时序 adapter 改善部分排序指标，但未超过 E6 的 R@1 |

表 3-X 表明，本文方法的提升不是由单一模块偶然造成的。固定 alignment teacher 与 multiview features 首先证明了局部对齐监督和多视角视频证据的有效性；随后，query-aware multiview 将固定融合改为按查询语义动态调整视角权重，使复杂查询能够获得更充分的局部证据；error-driven pairwise teacher 则进一步把近邻失败样本转化为成对排序监督，让模型直接学习正确视频与相似错误候选之间的差别。full 1kA 结果中，E5 相较 E4 在 R@1、R@5、R@10 和 MnR 上均有改善，说明改进已经作用到 student adapter 本身，而不是只依赖后处理分数校正。

同时，E6 与 E7 的结果也揭示了一个值得注意的现象：若以 R@1 为核心指标，E6 的增强评分效果最好；若关注更宽范围的候选质量，E7 在 R@5、R@10 和 MnR 上更占优。这说明局部对齐增强对不同排序指标的作用并不完全一致。对于本文任务而言，首位排序是最重要的报告指标，因此最终主结果采用 E6；而 E7 可作为系统推理权重调节的补充实验，说明该方法在候选列表整体质量上仍有优化空间。

E8 的结果表明，借鉴 BT-Adapter 的轻量时序分支可以改善部分排序指标，但对 R@1 的提升并不稳定。这一结果说明，简单增加 temporal adapter 并不一定能解决首位排序问题；真正决定 Top-1 的，仍然是查询语义成分与视频局部证据之间是否建立了可靠对应关系。因此，本文最终将 query-aware multiview、alignment teacher 和 pairwise teacher 作为核心算法路线，而将 BT-style temporal adapter 作为扩展消融结果进行讨论。

## 五、第三章可直接粘贴的结论段

综合公开方法对比和本文内部消融，可以得出如下结论。第一，本文方法并不是简单堆叠 rewrite、rerank、teacher 和 adapter，而是围绕“相似候选内部的局部语义区分”这一瓶颈展开。第二，查询感知多视角融合继承了 X-Pool 中“不同查询应关注不同视频证据”的思想，但本文将其用于轻量学生模型的表示增强，而不是单纯作为在线聚合模块。第三，错误驱动成对教师监督借鉴了 X-CoT 和 pairwise ranking 的思想，将大语言模型或教师模型的语义判断转化为离线训练信号，避免了在线重排序带来的高成本。第四，full 1kA 消融结果显示，本文方法能够在正式协议下带来稳定增益，说明其作用不仅限于小规模 q200 快速验证。

从论文贡献角度看，本文最重要的创新点可以概括为：提出了一种查询感知多视角对齐与错误驱动成对教师监督相结合的轻量视频检索增强方法。该方法在保持 FAISS 向量召回和 student adapter 可部署性的基础上，使模型能够利用更细的视频侧证据，并针对 near-failure 样本学习更清晰的排序边界。相比只做查询改写或候选重排序，这一方法更直接地改善了跨模态表示空间本身；相比全量交叉编码和在线大模型推理，它又具有更低的系统部署成本。

## 六、插图与插入位置建议

### 图 3-X  公开方法与本文方法 R@1 对比图

插入位置：表 3-X 之后。

绘制内容：横轴为 CLIP、X-CoT、TVTSv2、本文 Stage4、BT-Adapter、ViCLIP、CLIP4Clip、X-Pool、X-CoT+X-Pool；纵轴为 R@1。本文方法使用深色突出，公开方法使用浅灰或浅蓝。图注中说明不同方法训练设置不完全一致，该图用于展示性能区间和方法定位。

### 图 3-X  本文细粒度增强方法消融折线图

插入位置：表“本文细粒度增强方法消融结果”之后。

绘制内容：横轴为 E4、E5、E6、E7、E8；纵轴为 Recall；用三条线分别表示 R@1、R@5、R@10。建议突出 E4 到 E6 的 R@1 改善，以及 E7 在 R@5/R@10 上的补充优势。

### 图 3-X  查询感知多视角对齐与 pairwise teacher 框架图

插入位置：3.4 或 3.6.7 前。

绘制内容：左侧为文本查询和语义成分拆分，中间为全局视角、局部帧视角、时间窗视角，右侧为 student adapter；下方增加 near-failure 样本对，标注正确视频 `v+` 和错误候选 `v-`，用 pairwise loss 连接到 student。全部中文标注，白底，宋体，黑灰线框，核心模块使用浅蓝或浅橙描边。

## 七、参考文献与引用位置建议

1. CLIP4Clip：用于支撑“CLIP 迁移到视频文本检索任务后成为经典强基线”。  
   链接：https://github.com/ArrowLuo/CLIP4Clip

2. X-Pool：用于支撑“文本查询应关注与其语义最相关的视频帧或视频片段”。  
   链接：https://openaccess.thecvf.com/content/CVPR2022/papers/Gorti_X-Pool_Cross-Modal_Language-Video_Attention_for_Text-Video_Retrieval_CVPR_2022_paper.pdf

3. X-CoT：用于支撑“LLM CoT 推理可用于增强复杂视频文本匹配”。  
   链接：https://pmc.ncbi.nlm.nih.gov/articles/PMC13038389/

4. BT-Adapter：用于支撑“参数高效 adapter 可迁移到视频相关任务并保持较低训练成本”。  
   链接：https://openaccess.thecvf.com/content/CVPR2024/papers/Liu_BT-Adapter_Video_Conversation_is_Feasible_Without_Video_Instruction_Tuning_CVPR_2024_paper.pdf

5. InternVid / ViCLIP：用于支撑“强视频语言预训练模型能够提供更高质量的跨模态监督信号”。  
   链接：https://proceedings.iclr.cc/paper_files/paper/2024/hash/b7bfab38ed694b43e8c20c14f6c0e900-Abstract-Conference.html

建议引用位置：

- 在 `1.2.2 跨模态视频文本检索研究现状` 中，介绍 CLIP4Clip、X-Pool、ViCLIP 时分别加入上述文献。
- 在 `1.2.4 细粒度对齐与反馈学习研究现状` 中，介绍 X-CoT 和 pairwise teacher 思想时加入 X-CoT 文献。
- 在 `3.6.6 近年方法性能对比与本文方法定位` 的表格标题或表格说明段落后加入 CLIP4Clip、X-Pool、X-CoT、BT-Adapter 和 ViCLIP 对应引用。
- 在 `3.6.7 本文算法消融实验汇总` 的结论段中引用 X-Pool 与 X-CoT，用于说明本文方法和近年思想之间的继承关系。
