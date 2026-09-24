# ENGLISH figures for the manuscript (generated from 06_figures.py). Hình 1–2: kết quả định trước (protocol v0.4). Hình 3–4: HẬU KIỂM (ghi rõ trên hình).
# Chạy từ thư mục gốc: python notebooks/06_figures.py
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures_en"
FIG.mkdir(exist_ok=True)
C = {"AUG": "#2a78d6", "PS": "#eb6834", "BASE": "#1baf7a"}   # đã kiểm bằng validate_palette.js
MK = {"AUG": "o", "PS": "s", "BASE": "^"}
LAB = {"AUG": "Block-masking augmentation (M-AUG)", "PS": "Pattern submodels (M-PS)", "BASE": "No missing-data handling (M-BASE)"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
SC_LAB = {"S0": "S0 complete data", "S1": "S1 anthropometry missing", "S2": "S2 blood pressure missing",
          "S3": "S3 medical history missing", "S4": "S4 lifestyle/SES missing", "S5": "S5 anthropometry + BP missing",
          "S6": "S6 history + lifestyle missing*", "S7": "S7 lifestyle missing (MAR)*"}


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


# ---- Hình 1: Brier skill theo kịch bản (định trước)
t = pd.read_csv(ROOT / "final_out" / "L_table_LR.csv")
sc = list(SC_LAB)
fig, ax = plt.subplots(figsize=(7.2, 3.9))
for i, m in enumerate(["AUG", "PS", "BASE"]):
    d = t[t.model == f"LR-{m}"].set_index("scenario").loc[sc]
    y = [k + (i - 1) * 0.22 for k in range(len(sc))]
    ax.errorbar(d.skill, y, xerr=[d.skill - d.skill_lo, d.skill_hi - d.skill], fmt=MK[m], ms=5,
                color=C[m], ecolor=C[m], elinewidth=1.2, capsize=0, label=LAB[m])
ax.axvline(0, color=INK2, lw=0.8)
ax.set_yticks(range(len(sc)), [SC_LAB[s] for s in sc])
ax.invert_yaxis()
ax.grid(axis="x", color=GRID, lw=0.6)
ax.set_xlabel("Survey-weighted Brier skill (95% CI, JK2)")
ax.set_title("Figure 1. Performance in NHANES 2021–2023 by block-missing scenario (HbA1c ≥6.5%)",
             loc="left", fontsize=9.5, color=INK, pad=22)
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=8)
fig.text(0.01, -0.02, "* S6, S7: prespecified secondary scenarios; S6 was not used in M-AUG training.",
         fontsize=7.5, color=INK2)
save(fig, "fig1_skill_by_scenario")

# ---- Hình 2: forest plot Δ (M-AUG − M-PS), biên tương đương ±0,005 (định trước)
r = json.loads((ROOT / "final_out" / "L_results.json").read_text(encoding="utf-8"))
rows = [(SC_LAB[s], r["primary"][f"delta_{s}"]) for s in ["S1", "S2", "S3", "S4", "S5"]]
rows += [(SC_LAB["S6"], r["secondary"]["LR AUG−PS tại S6 (không dùng khi huấn luyện AUG)"]),
         (SC_LAB["S7"], r["secondary"]["LR AUG−PS tại S7 (MAR)"]),
         ("Mean S1–S5 (primary estimand)", r["primary"]["delta_mean_S1_S5"])]
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.axvspan(-0.005, 0.005, color="#efeeea", zorder=0)
ax.text(0.0048, len(rows) - 0.5, "equivalence region ±δ", ha="right", va="center", fontsize=7.5, color=INK2)
for k, (lab, v) in enumerate(rows):
    main = k == len(rows) - 1
    ax.errorbar(v["est"], k, xerr=[[v["est"] - v["lo"]], [v["hi"] - v["est"]]],
                fmt="D" if main else "o", ms=7 if main else 5, color=C["AUG"] if main else INK2,
                elinewidth=1.6 if main else 1.1, capsize=0)
    ax.text(0.0102, k, f"{v['est']:+.4f} ({v['lo']:+.4f}, {v['hi']:+.4f})", va="center", fontsize=7.5,
            color=INK)
ax.axvline(0, color=INK2, lw=0.8)
ax.set_yticks(range(len(rows)), [x[0] for x in rows])
ax.set_ylim(-0.6, len(rows) + 0.05)
ax.invert_yaxis()
ax.set_xlim(-0.011, 0.0175)
ax.set_xlabel("Δ Brier skill (M-AUG − M-PS); >0 favours augmentation")
ax.set_title("Figure 2. Primary comparison: augmentation vs pattern submodels (prespecified δ = 0.005)", loc="left",
             fontsize=9.5, color=INK)
save(fig, "fig2_forest_primary")

# ---- Hình 3 (HẬU KIỂM): thiếu một phần nhân trắc
ph = json.loads((ROOT / "posthoc_out" / "posthoc_results.json").read_text(encoding="utf-8"))["PH1b"]
items = [("Measured weight, height and waist", "S0_full"), ("No tape measure (measured weight + height)", "A1_no_tape"),
         ("Self-reported weight and height only", "A2_self_report"), ("No anthropometry", "S1_no_anthro")]
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.6), sharey=True)
for ax, met, xl in [(axs[0], "skill", "Brier skill"), (axs[1], "auc", "AUROC")]:
    for k, (lab, key) in enumerate(items):
        v = ph[f"{met}_{key}"]
        ax.errorbar(v["est"], k, xerr=[[v["est"] - v["lo"]], [v["hi"] - v["est"]]], fmt="o", ms=5,
                    color=C["AUG"], elinewidth=1.2)
        ax.text(v["hi"], k, f"  {v['est']:.3f}", va="center", fontsize=7.5, color=INK)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_xlabel(xl + " (95% CI, JK2)")
axs[0].set_yticks(range(len(items)), [x[0] for x in items])
axs[0].invert_yaxis()
fig.suptitle("Figure 3 (post hoc). Source of anthropometric information and performance — LR submodels, HbA1c ≥6.5%",
             x=0.01, y=1.04, ha="left", fontsize=9.5, color=INK)
axs[0].set_xlim(right=0.068); axs[1].set_xlim(right=0.885)
save(fig, "fig3_posthoc_anthropometry")

# ---- Hình 4 (HẬU KIỂM): DCA nhãn ≥5,7
d = pd.read_csv(ROOT / "posthoc_out" / "PH2_dca.csv")
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.plot(d.t, d["LR57-AUG S0"], color=C["AUG"], lw=2, label="Model (M-AUG), complete data")
ax.plot(d.t, d["LR57-AUG S1"], color=C["AUG"], lw=2, ls=(0, (4, 2)), label="Model (M-AUG), anthropometry missing")
ax.plot(d.t, d["Bang ≥4"], color=C["PS"], lw=2, label="Bang score ≥4")
ax.plot(d.t, d["Xét nghiệm tất cả"], color=INK2, lw=1.2, label="Test all")
ax.axhline(0, color=INK2, lw=0.8, label="Test none")
ax.set_ylim(-0.05, 0.3)
ax.set_xlim(0.05, 0.6)
ax.grid(color=GRID, lw=0.6)
ax.set_xlabel("Threshold probability for referral to HbA1c testing")
ax.set_ylabel("Net benefit (survey-weighted)")
ax.set_title("Figure 4 (post hoc). Decision curve analysis, HbA1c ≥5.7%, NHANES 2021–2023",
             loc="left", fontsize=9.5, color=INK)
ax.legend(frameon=False, fontsize=7.5, loc="upper right")
save(fig, "fig4_posthoc_dca_57")
print("Đã lưu:", sorted(p.name for p in FIG.iterdir()))
