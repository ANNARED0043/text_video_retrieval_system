# 项目瓶颈诊断报告

## 1. 当前结论

在当前项目链路下，`q500 teacher` 已经是较优蒸馏规模基线，继续扩大到 `q800`、引入动态温度、或引入轻量结构化 prototype 奖励，都没有带来稳定的额外增益。

当前最优结果仍然是：
- `R@1 = 48.5`
- `R@5 = 66.5`
- `R@10 = 73.5`

这说明系统瓶颈不再主要来自“训练样本数量不足”或“蒸馏参数没有调好”，而是来自更深层的监督与表示限制。

## 2. 运行链路中的关键瓶颈

### 2.1 Teacher supervision 覆盖率不足

当前 ViCLIP teacher supervision 的构建方式是：
- 先由学生检索器召回 top30 候选
- 再由 ViCLIP 对这些候选做重排
- 最后保留 top10 作为 teacher targets

这会带来一个硬上限：
- 如果 ground-truth 本来就不在学生召回候选里，teacher 根本无法提供正确监督

在 `q500` teacher 文件上统计发现：
- 共 500 条训练样本
- 只有 304 条的 ground-truth 出现在 teacher targets 中
- 只有 120 条的 teacher top1 就是 ground-truth
- 有 196 条样本连 ground-truth 都不在 teacher top10 中

### 2.2 Teacher 分布区分度弱

对 `q500` teacher targets 的分数分布统计显示：
- top1-top2 平均差距很小
- 中位差距更小
- top-k 熵接近满熵

这说明 teacher 在当前候选集合上的排序分布比较平，缺乏强区分性。

### 2.3 Student 可学习容量主要集中在文本侧

当前系统中的可训练主体基本是一个轻量文本残差适配器。

这意味着：
- query 表示在变化
- video 表示基本固定
- cross-modal alignment 的提升空间主要被压缩在 query 侧

但根据 2024-2025 前沿工作，视频检索的关键问题并不只在语言侧，而是同时存在：
- vision discrepancy
- language discrepancy
- alignment discrepancy

### 2.4 当前 prototype 仍主要是词级奖励

即使已经扩展到 `action/object/scene`，当前 prototype 第一版仍然更接近规则抽取与奖励项，而不是 embedding-level prototype learning。

### 2.5 训练样本筛选与训练轮次共同压缩了学习空间

当前主实验中常见配置为：
- `max_train_queries = 500`
- `train_rows_used = 396`
- `epochs = 1`

这意味着真正进入训练的样本并不多，多数新方法都在同一批样本上进行轻量扰动。

## 3. 与前沿工作的差异

### 3.1 TeachCLIP / Holistic Features 系列

相关工作指出：
- 文本到视频检索的提升不只取决于文本表示本身
- 还取决于 frame relevance 与更合理的视频聚合方式

### 3.2 T-MASS

T-MASS 的重要启发是：
- 文本查询不应总被视为单点 embedding
- 含混 query 的语义本身具有随机性和分布性

### 3.3 MV-Adapter / DiscoVLA

这两类工作共同指出：
- 参数高效视频检索的提升，往往来自视频、语言与对齐三方面联合适配
- 不是单独对 query 做小型残差微调就能持续提升

## 4. 当前真正的主瓶颈

综合当前实验与代码链路，主瓶颈可以收束为三点：

1. Teacher supervision 不完整
2. Teacher supervision 不够强
3. Student 结构过弱，尤其是视频聚合与跨模态对齐没有被真正建模

## 5. 后续最值得投入的方向

### 方向 A：视频侧轻量聚合适配

目标：
- 不重做大规模视频编码
- 直接在现有 segment features 上提升视频聚合能力

建议做法：
- 从单一 mean pooling 升级为可学习的 mean/max 或 temporal attention 聚合
- 由 query 控制视频聚合权重

### 方向 B：更高覆盖率的 teacher supervision

目标：
- 提升 teacher 中正样本出现率

### 方向 C：真正的表示级 prototype learning

目标：
- 将 prototype 从词级奖励升级为 embedding-level 原型中心约束

## 6. 当前建议

当前最合理的研究路线不是继续增加蒸馏规模，而是：

1. 以 `q500 teacher` 作为稳定基线
2. 优先探索视频侧轻量聚合适配
3. 再提升 teacher coverage
4. 最后再将 prototype 做成真正的表示级模块
