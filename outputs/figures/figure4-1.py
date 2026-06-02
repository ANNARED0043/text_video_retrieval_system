from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT = Path("outputs/figures")
OUT.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis("off")

def box(x, y, w, h, text, fc="#f8f4ee", ec="#2b5d7e", fs=10, weight="normal"):
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=1.8)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight=weight)

def arrow(x1, y1, x2, y2):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=13,
            linewidth=1.6,
            color="#444444",
        )
    )

# Layer titles
ax.text(0.4, 8.9, "Data & Representation Layer", fontsize=11, fontweight="bold", color="#2b5d7e")
ax.text(0.4, 6.9, "Index & Retrieval Layer", fontsize=11, fontweight="bold", color="#2b5d7e")
ax.text(0.4, 5.0, "Semantic Enhancement Layer", fontsize=11, fontweight="bold", color="#2b5d7e")
ax.text(0.4, 3.0, "Representation Enhancement & Continual Learning Layer", fontsize=11, fontweight="bold", color="#2b5d7e")
ax.text(0.4, 1.0, "Interaction & Result Management Layer", fontsize=11, fontweight="bold", color="#2b5d7e")

# Row 1
box(0.8, 7.8, 2.0, 0.8, "Raw Videos", fc="#fff7ef", weight="bold")
box(3.2, 7.8, 2.2, 0.8, "Annotations / Queries", fc="#fff7ef")
box(5.8, 7.8, 2.0, 0.8, "Manifest", fc="#eef5fb")
box(8.2, 7.8, 2.3, 0.8, "Segment Features", fc="#eef5fb")
box(10.9, 7.8, 2.1, 0.8, "Multiview / Teacher Files", fc="#eef5fb")

# Row 2
box(1.3, 5.9, 2.2, 0.8, "Text Encoder", fc="#fdf1e8")
box(4.0, 5.9, 2.2, 0.8, "FAISS Index", fc="#fdf1e8")
box(6.7, 5.9, 2.5, 0.8, "Baseline Retrieval", fc="#eef8f1")
box(9.7, 5.9, 2.2, 0.8, "Video Aggregation", fc="#eef8f1")

# Row 3
box(1.0, 4.0, 2.2, 0.8, "Ambiguity Scoring", fc="#f7eef9")
box(3.7, 4.0, 2.2, 0.8, "Selective Rewrite", fc="#f7eef9")
box(6.4, 4.0, 2.0, 0.8, "Rewrite Cache", fc="#f7eef9")
box(8.9, 4.0, 2.3, 0.8, "Candidate Optimization", fc="#fff1f1")
box(11.7, 4.0, 1.7, 0.8, "Rerank Cache", fc="#fff1f1")

# Row 4
box(0.9, 2.0, 2.2, 0.8, "Alignment Teacher", fc="#eef5fb")
box(3.5, 2.0, 2.2, 0.8, "Multiview Features", fc="#eef5fb")
box(6.1, 2.0, 2.1, 0.8, "Failure Diagnosis", fc="#fdf1e8")
box(8.6, 2.0, 2.0, 0.8, "Feedback Teacher", fc="#fdf1e8")
box(11.0, 2.0, 2.0, 0.8, "Acceptance Gate", fc="#eef8f1")

# Row 5
box(0.8, 0.2, 2.3, 0.8, "Experiment Scripts", fc="#fff7ef")
box(3.5, 0.2, 2.3, 0.8, "Summary / Checkpoints", fc="#fff7ef")
box(6.2, 0.2, 2.0, 0.8, "Research Logs", fc="#fff7ef")
box(8.6, 0.2, 2.0, 0.8, "Front-end UI", fc="#fff7ef")
box(11.0, 0.2, 2.0, 0.8, "History / Feedback", fc="#fff7ef")

# Horizontal arrows
for y in [8.2, 6.3, 4.4, 2.4, 0.6]:
    for x1, x2 in [(2.8, 3.2), (5.4, 5.8), (7.8, 8.2), (10.5, 10.9)]:
        if y in [6.3] and x2 == 10.9:
            continue
        arrow(x1, y, x2, y)

# Vertical arrows between layers
arrow(6.8, 7.8, 6.8, 6.7)
arrow(6.8, 5.9, 6.8, 4.8)
arrow(10.0, 4.0, 10.0, 2.8)
arrow(10.0, 2.0, 10.0, 1.0)

# Protocol line
ax.plot([0.8, 13.0], [9.5, 9.5], color="#d64b3b", linewidth=2.2)
ax.text(1.0, 9.72, "safe_train: learning & feedback teacher", color="#d64b3b", fontsize=9, fontweight="bold")
ax.text(5.1, 9.72, "safe_dev: selection & promotion", color="#d64b3b", fontsize=9, fontweight="bold")
ax.text(9.1, 9.72, "1kA: locked reporting", color="#d64b3b", fontsize=9, fontweight="bold")

plt.title("Figure 4-1 System Architecture of Natural Language Video Retrieval", fontsize=13)
plt.tight_layout()
plt.savefig(OUT / "Figure4_1_system_architecture.png", dpi=220)
print(f"saved: {OUT / 'Figure4_1_system_architecture.png'}")