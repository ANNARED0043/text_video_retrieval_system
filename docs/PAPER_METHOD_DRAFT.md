# 论文方法设计稿草案

## 题目方向

建议题目方向：
- 面向自然语言视频检索的不确定性感知原型蒸馏方法

英文可写为：
- Uncertainty-Aware Prototype Distillation for Text-to-Video Retrieval

## 1. 研究问题

当前自然语言视频检索系统虽然可以通过更强教师模型和更大规模蒸馏数据获得提升，但仍然存在三个核心问题：

1. 查询语义不确定性没有被显式建模。
文本查询往往具有含混性、歧义性与语义压缩现象，例如动作主体、省略场景、弱约束对象等。现有方法通常将 query 编码为单点表示，容易导致蒸馏监督过硬，进而限制泛化能力。

2. 教师监督主要停留在候选排序层，缺少结构化语义迁移。
当前 teacher supervision 更多表现为 top-k 排序分数、hard negatives 和少量 prototype terms，尚未形成稳定的动作、对象、场景三级语义原型监督。

3. 持续学习中的记忆更新缺少置信控制。
若将不稳定样本直接写入 prototype memory 或 hard negative memory，容易造成错误记忆累积，影响后续训练。

## 2. 方法核心思想

本项目建议收束为一个统一的方法框架，而不是继续堆叠独立模块：

- 不确定性感知
- 原型蒸馏
- 记忆门控更新

统一方法名建议为：
- UAPD: Uncertainty-Aware Prototype Distillation

核心思想是：
- 先估计每个 query 的语义不确定性；
- 再根据不确定性调整 teacher soft labels 的蒸馏强度；
- 同时从 teacher 高置信候选中抽取结构化 prototype；
- 最后仅对高置信 prototype 执行门控式 memory 更新。

该方法的关键不是多加若干 loss，而是围绕“query 不确定性如何决定蒸馏与记忆更新策略”建立统一机制。

## 3. 方法结构

### 3.1 Query Uncertainty Estimation

目标：
- 判断一个文本查询是明确查询还是含混查询。

可计算的不确定性信号包括：
- teacher top1 与 top2 的分数差
- teacher top-k 分布熵
- query 中动作词、对象词、场景词覆盖度
- rewrite 模块给出的候选释义数量

定义：
- 分数间隔越小，不确定性越高
- teacher 分布越平，不确定性越高
- query 语义槽位越缺失，不确定性越高

建议形成一个归一化不确定性分数：
- `u(q) in [0, 1]`

其中：
- `u(q)` 越大，表示 query 越含混
- `u(q)` 越小，表示 query 越明确

### 3.2 Uncertainty-Aware Teacher Distillation

目标：
- 让 teacher supervision 的强度与 query 的不确定性匹配。

基本策略：
- 明确 query：蒸馏分布更尖锐，突出精确匹配
- 含混 query：蒸馏分布更平滑，保留更多暗知识

可采用自适应温度：
- `tau(q) = tau_min + u(q) * (tau_max - tau_min)`

其中：
- `tau_min` 用于明确 query
- `tau_max` 用于含混 query

这样 teacher soft labels 不再是固定温度，而是由 query 语义状态动态决定。

进一步可加权蒸馏损失：
- 含混 query 更重视 listwise 分布
- 明确 query 更重视 top1 / top-k 排名

### 3.3 Structured Prototype Distillation

目标：
- 不再将 prototype 简化为 token overlap，而是建立结构化语义原型。

建议将 prototype 拆成三类：
- action prototype
- object prototype
- scene prototype

构建方式：
- 从 teacher top positives 中抽取稳定共现语义
- 对每条 query 生成三类 prototype target
- 在 embedding space 中维护 prototype center

训练时的作用：
- 约束 query 表示不仅接近正视频，还接近对应的动作、对象、场景原型中心
- 对含混 query 保留多个候选 prototype，而非只保留单一词项

这一部分是当前系统从“关键词奖励”走向“可写论文的方法模块”的关键。

### 3.4 Memory-Gated Prototype Update

目标：
- 将 Stage 2 的 prototype distillation 自然延伸到 Stage 3 的 continual learning。

核心机制：
- 不是所有 prototype 都写入 memory
- 只有高置信 query、稳定 teacher 排序、稳定 prototype 匹配的样本才允许更新 memory

可设计门控分数：
- `g(q) = 1 - u(q)`

当以下条件满足时才更新：
- query uncertainty 低
- teacher top-k 排序稳定
- prototype overlap 高
- 当前样本不是疑似异常样本

更新对象包括：
- prototype memory
- hard negative memory
- constraint memory

这样可以避免错误 prototype 被不断强化。

## 4. 损失函数设计草案

建议总损失写为：

`L = L_rank + lambda1 * L_soft(q) + lambda2 * L_proto(q) + lambda3 * L_memory(q)`

其中：

- `L_rank`
  - 基础检索损失
  - 可为 cross-entropy 或 contrastive ranking loss

- `L_soft(q)`
  - 不确定性感知 soft-label distillation
  - 其温度由 `u(q)` 决定

- `L_proto(q)`
  - 原型对齐损失
  - 约束 query 与 action/object/scene prototypes 的匹配

- `L_memory(q)`
  - 记忆门控约束项
  - 仅在高置信样本上激活

可进一步写成：

- `L_soft(q) = KL(p_teacher^tau(q) || p_student)`
- `L_proto(q) = sum_c d(z_q, p_c)`

其中：
- `c` 表示 prototype 类别
- `p_c` 表示某类 prototype center
- `z_q` 表示 query 表征

## 5. 与现有代码的对应改造点

### 第一阶段：轻量可落地版本

目标：
- 控制本地运行时间不超过 3 小时
- 在现有工程基础上先做最小可验证版本

优先改造点：

1. 在 `build_viclip_teacher_supervision.py` 中新增 uncertainty 字段
- 保存 top1-top2 gap
- 保存 teacher top-k entropy
- 保存 query 的原型槽位覆盖信息

2. 在 `run_stage_experiment.py` 中新增自适应温度
- 固定温度改为 query-aware temperature
- 根据 uncertainty 调整 `teacher_temperature`

3. 在 `semantic_memory.py` 中新增结构化 prototype 抽取
- 从 query 中拆 action/object/scene
- 原型不再只存 token 频次

4. 在 `text_adapter.py` 中新增 prototype alignment term
- 不再只是 prototype bonus
- 改为 prototype center 的相似度约束

### 第二阶段：论文增强版本

在轻量版本有效后再加入：

1. 多原型候选保留
- 含混 query 允许多个 prototype 并存

2. 门控式 memory 更新
- 只把高置信样本写入 memory

3. uncertainty-aware hard negative policy
- 明确 query 使用更强负样本
- 含混 query 使用更保守负样本

## 6. 实验设计建议

建议收束为以下实验链路：

1. Baseline
- 原始 ViT-H-14 检索结果

2. Stage 2 Distillation Baseline
- ViCLIP teacher + q500
- ViCLIP teacher + q800

3. + Uncertainty-Aware Distillation
- 观察固定温度与自适应温度差异

4. + Structured Prototype Distillation
- 验证 action/object/scene prototype 的贡献

5. + Memory-Gated Update
- 验证记忆机制对持续学习阶段的提升

建议固定评测口径：
- 训练：safe_train
- 调参验证：safe_dev
- 封闭评测：1kA q200

## 7. 论文贡献点草案

建议论文贡献写成三点：

1. 提出一种面向自然语言视频检索的不确定性感知蒸馏框架。
- 通过显式建模 query uncertainty，动态调整 teacher supervision 的蒸馏温度与监督强度。

2. 提出一种结构化 prototype distillation 机制。
- 将 teacher 监督从单纯排序分数扩展到 action、object、scene 三类语义原型迁移。

3. 提出一种记忆门控更新策略。
- 仅对高置信样本执行 prototype memory 与 hard negative memory 更新，提升持续学习稳定性。

## 8. 下一步执行顺序

为了控制本地运行时间，建议按下面顺序推进：

1. 先完成 `q800 teacher supervision`
2. 实现 uncertainty 字段与 query-aware temperature
3. 先做轻量版 structured prototype
4. 固定 `1kA q200` 做统一对比
5. 若有效，再推进 memory-gated continual update

## 9. 当前建议

当前最值得押注的主创新不是 rewrite 或 rerank，也不是单独强化 hard negatives，而是：

- 不确定性感知原型蒸馏

这是因为它：
- 能统一 Stage 2 与 Stage 3
- 能自然吸收 2024-2026 前沿论文的思想
- 能形成较完整的方法图、公式与消融实验
- 能在现有工程基础上逐步落地
