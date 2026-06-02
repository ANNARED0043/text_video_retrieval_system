# Auto Continual Learning Feedback: 20260424_001926_hybrid_elite_1kA

- Strategy: `hybrid_elite`
- Basis: DiscoVLA CVPR 2025, TokenBinder WACV 2025, MAMA 2026
- Eval split: `1kA`
- Quality success rate: 0.0%
- Promotion success rate: 0.0%
- Target 80% met: no
- Acceptance reference: active best summary, not the candidate run baseline

## Round Results

### Round 1

- Selected candidate: `round01_c02`
- Accepted by quality gate: False
- Promoted by active-best gate: False
- Delta vs active best: R@1 -0.5, R@5 0.5, R@10 0.5
- Reason: Rejected by quality gate: R@1 gain vs active best is below min_quality_r1_gain=0.01.

### Round 2

- Selected candidate: `round02_c02`
- Accepted by quality gate: False
- Promoted by active-best gate: False
- Delta vs active best: R@1 -0.5, R@5 0.5, R@10 0.5
- Reason: Rejected by quality gate: R@1 gain vs active best is below min_quality_r1_gain=0.01.

### Round 3

- Selected candidate: `round03_c02`
- Accepted by quality gate: False
- Promoted by active-best gate: False
- Delta vs active best: R@1 -0.5, R@5 0.5, R@10 0.5
- Reason: Rejected by quality gate: R@1 gain vs active best is below min_quality_r1_gain=0.01.

## Interpretation

A round is useful only when it improves over the active best.
Rejected candidates are logged but never overwrite the current best.
Use `v35_plus` when the goal is to improve the current 50.5 R@1 case. `safe_dev` runs are diagnostic and are not comparable with the locked 1kA number.
