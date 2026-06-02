# Auto Continual Learning Feedback: 20260423_213906_hybrid_elite_safe_dev

- Strategy: `hybrid_elite`
- Basis: DiscoVLA CVPR 2025, TokenBinder WACV 2025, MAMA 2026
- Eval split: `safe_dev`
- Quality success rate: 0.0%
- Promotion success rate: 0.0%
- Target 80% met: no

## Round Results

### Round 1

- Selected candidate: `round01_c01`
- Accepted by quality gate: False
- Promoted by active-best gate: False
- Delta vs run baseline: R@1 None, R@5 None, R@10 None
- Reason: Rejected by quality gate: R@1 gain is below min_quality_r1_gain=0.01.

## Interpretation

本次学习只会把通过 gate 的候选视为有效学习；未通过的候选已经记录，但不会覆盖当前最佳状态。
如果 quality success rate 低于 80%，建议继续使用 `hybrid_elite`，或降低每轮训练规模先做策略筛选。
