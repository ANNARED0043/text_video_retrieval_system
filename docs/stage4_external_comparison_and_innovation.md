# 第三章补充：近年方法对比与本文创新优势表述

## 1. 对比原则

本文需要与 CLIP4Clip、X-Pool、X-CoT、BT-Adapter、ViCLIP 等近年相关方法进行对比，但对比时必须区分“公开横向性能比较”和“本文内部受控消融”。公开方法通常使用不同的骨干网络、预训练规模、训练策略和评测设置，如果直接将本文 q200 消融结果与公开 full 1kA 结果并列，会造成协议不一致。因此，本文建议采用两张表组织实验结论：

第一张表用于公开横向定位，只使用 full 1kA 或公开论文中相同协议下的结果。该表的作用不是宣称本文超过所有强方法，而是说明本文方法在轻量 adapter 与本地可运行约束下具有明确竞争力。

第二张表用于本文核心创新验证，比较 baseline、固定 alignment + multiview、query-aware multiview、error-driven pairwise teacher 等阶段。该表用于证明本文方法的增益来自算法设计本身，而不是偶然参数波动或后处理堆叠。

## 2. 公开方法对比表建议

**表 3-X  MSR-VTT 1kA 文本到视频检索公开方法对比**

| 方法 | 年份 | 方法类型 | R@1 | R@5 | R@10 | 说明 |
|---|---:|---|---:|---:|---:|---|
| BT-Adapter | 2024 | 参数高效迁移 / adapter-based | 40.9 | 64.7 | 73.5 | 面向视频任务的轻量迁移方法 |
| CLIP4Clip | 2021 | CLIP full fine-tuning | 44.5 | 71.4 | 81.6 | 经典 CLIP 视频检索强基线 |
| X-Pool | 2022 | query-aware fine-grained pooling | 46.9 | 72.8 | 82.2 | 引入查询感知的视频帧聚合 |
| X-CoT + X-Pool | 2025 | LLM reasoning enhanced retrieval | 47.3 | 73.3 | - | 利用推理增强候选语义判断 |
| 本文 Stage3 | 2026 | alignment teacher + fixed multiview | 38.7 | 61.1 | 70.9 | 本地轻量 adapter，固定多视角融合 |
| 本文 Stage4 | 2026 | query-aware multiview + pairwise teacher | 39.1 | 61.6 | 72.1 | 纯 student adapter 结果 |
| 本文 Stage4（系统增强） | 2026 | query-aware multiview + alignment scoring | 39.7 | 61.3 | 71.6 | adapter 结合局部对齐增强评分 |

需要注意的是，CLIP4Clip、X-Pool 等方法通常采用更完整的训练流程和更强的公开训练设置，本文方法没有在相同规模下复现其全部训练过程。因此，本文不宜声称“全面超过 X-Pool 或 CLIP4Clip”。更准确的表述应为：本文方法在轻量双塔检索系统中吸收了查询感知聚合和推理式成对监督思想，并在 full 1kA 正式协议下获得稳定正向增益，说明该方向具有有效性和进一步扩展潜力。

## 3. 本文核心消融表建议

**表 3-X  本文细粒度增强算法消融结果**

| 阶段 | 主要改动 | 评测协议 | R@1 | R@5 | R@10 | MnR | 结论 |
|---|---|---|---:|---:|---:|---:|---|
| E0 | 原始 baseline | q200 | 47.5 | 65.0 | 72.0 | 17.32 | 双塔召回具备基础能力，但 Top-1 仍有提升空间 |
| E1 | alignment teacher + fixed multiview | q200 | 50.5 | 64.5 | 73.5 | 20.42 | 固定多视角融合显著改善 Top-1 |
| E2 | query-aware multiview + pairwise teacher | q200 | 49.0 | 66.5 | 75.5 | 20.205 | 纯 adapter 对 Top-5/Top-10 改善明显，但 Top-1 不稳定 |
| E3 | E2 + alignment/multiview 系统增强 | q200 | 51.0 | 66.5 | 75.0 | 20.72 | 查询感知局部证据进一步改善首位校准 |
| E4 | alignment teacher + fixed multiview | full 1kA | 38.7 | 61.1 | 70.9 | 29.112 | 上一阶段正式协议最优结果 |
| E5 | query-aware multiview + pairwise teacher | full 1kA | 39.1 | 61.6 | 72.1 | 28.269 | 纯 student adapter 获得稳定正向提升 |
| E6 | E5 + alignment/multiview 系统增强 | full 1kA | 39.7 | 61.3 | 71.6 | 28.478 | 当前正式协议下最优结果 |

从消融结果看，固定多视角融合已经能够提升 R@1，但其本质仍是将不同视频视角以近似固定方式补充到检索分数中。查询感知多视角融合进一步引入了文本条件，使模型能够根据查询中的动作、对象、关系和人物属性动态调整视频证据权重。错误驱动 pairwise teacher 则将 near-failure 样本转化为成对排序监督，使学生模型直接学习正确视频与相似错误候选之间的判别边界。

full 1kA 结果显示，本文 Stage4 纯 adapter 的 R@1 从 38.7% 提升到 39.1%，R@10 从 70.9% 提升到 72.1%，MnR 从 29.112 降低到 28.269；结合 alignment/multiview 系统增强评分后，R@1 进一步达到 39.7%。这说明本文方法不是只在 q200 快速验证中有效，而是在 locked 1kA 正式协议下同样带来了稳定收益。

## 4. 可直接写入论文的创新优势表述

与 X-Pool 相比，本文并未简单采用查询感知池化作为最终排序模块，而是将其嵌入多视角视频表示学习过程，使不同查询能够动态选择全局视角、局部帧视角和时间窗视角。与 X-CoT 相比，本文没有将大语言模型推理作为在线重排序组件，而是将其思想转化为离线 pairwise teacher，用于构造正确视频优于相似错误候选的排序监督。与 BT-Adapter 相比，本文同样保持了参数高效迁移的工程优势，但进一步引入了视频侧局部证据和错误驱动监督，使 adapter 学习不再局限于文本侧残差校正。与 ViCLIP 类视频语言 teacher 相比，本文更关注如何将强 teacher 的监督压缩到轻量 student 检索模型中，使系统能够在本地环境下保持较低部署成本。

因此，本文方法的优势并不在于简单追求最大模型规模，而在于形成了一条具有工程可行性的细粒度增强路线：首先利用 alignment teacher 提供局部语义对齐约束，再利用 multiview features 扩展视频侧证据，随后通过 query-aware attention 动态调度不同视频视角，最后通过 error-driven pairwise teacher 修正 near-failure 样本中的排序边界。实验结果表明，该路线能够在 full 1kA 协议下带来持续正向增益，说明本文提出的细粒度对齐增强方法具有明确有效性。

## 5. 引用位置建议

1. 在介绍 CLIP4Clip 时引用：  
   句子：CLIP4Clip 将 CLIP 迁移到视频文本检索任务中，并验证了 CLIP 图文预训练特征在视频检索中的有效性。  
   链接：https://github.com/ArrowLuo/CLIP4Clip

2. 在介绍 X-Pool 时引用：  
   句子：X-Pool 指出不同查询对视频帧的关注不同，因此提出查询感知的视频帧聚合机制。  
   链接：https://layer6.ai/publications/cvpr-2022-x-pool-cross-modal-language-video-attention-for-text-video-retrieval/

3. 在介绍 X-CoT 时引用：  
   句子：X-CoT 利用大语言模型的推理能力增强复杂视频文本匹配，为本文构造离线 pairwise teacher 提供了启发。  
   链接：https://aclanthology.org/2025.emnlp-main.1588/

4. 在介绍 BT-Adapter 时引用：  
   句子：BT-Adapter 说明参数高效迁移能够在不进行大规模视频指令微调的情况下改善视频相关任务表现。  
   链接：https://openaccess.thecvf.com/content/CVPR2024/papers/Liu_BT-Adapter_Video_Conversation_is_Feasible_Without_Video_Instruction_Tuning_CVPR_2024_paper.pdf

5. 在介绍 ViCLIP/InternVid 时引用：  
   句子：InternVid/ViCLIP 表明大规模视频文本预训练能够提供更强的视频语言监督信号。  
   链接：https://proceedings.iclr.cc/paper_files/paper/2024/hash/b7bfab38ed694b43e8c20c14f6c0e900-Abstract-Conference.html

