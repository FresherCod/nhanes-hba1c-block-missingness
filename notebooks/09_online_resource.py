# Tạo Online Resource 1 (tài liệu bổ sung) từ các kết quả đã xuất. Không phân tích mới.
# Chạy từ thư mục gốc: python notebooks/09_online_resource.py
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript" / "Online_Resource_1.md"
flow = pd.read_csv(ROOT / "audit_out" / "cohort_flow.csv")
miss = pd.read_csv(ROOT / "audit_out" / "missingness.csv")
cfg = json.loads((ROOT / "final_out" / "config_P.json").read_text(encoding="utf-8"))
rev = json.loads((ROOT / "posthoc_out" / "posthoc_review_results.json").read_text(encoding="utf-8"))
lock = json.loads((ROOT / "LOCK_protocol_v0.4.json").read_text(encoding="utf-8"))

L = []
w = L.append
w("---\ntitle: \"Online Resource 1\"\n---\n")
w("**Article:** One model or many? Handling missing blocks of non-laboratory information in a machine-learning "
  "screening tool for elevated HbA1c: a protocol-locked temporal validation in NHANES. *Health Information Science "
  "and Systems*. Author: Phuc Dinh Truong (truongdinhphucspkt@gmail.com).\n")

# S1 flow
steps = {"C1 in DEMO": "Participants in demographic file", "C2 age>=20": "Aged ≥20 years",
         "C3 MEC examined": "Examined in mobile examination center", "C4 has LBXGH": "Valid HbA1c result",
         "C5 label weight>0": "Positive HbA1c sample weight", "C6 not pregnant": "Not pregnant",
         "C7 not diagnosed (DIQ010)": "No self-reported diabetes diagnosis (DIQ010 not 1, 7, 9 or missing)",
         "C8 no diabetes pills": "Not taking oral glucose-lowering medication (DIQ070 ≠ 1)"}
w("## Table S1 Participant selection\n")
w("| Step | 2017–March 2020, n remaining | 2021–2023, n remaining |\n|---|---|---|")
for k, lab in steps.items():
    p = flow[(flow.cycle == "P") & (flow.step == k)].n.iat[0]
    l_ = flow[(flow.cycle == "L") & (flow.step == k)].n.iat[0]
    w(f"| {lab} | {p:,} | {l_:,} |")
w("\nBorderline diabetes (DIQ010 = 3) was retained; excluding it left 6,458 and 4,657 participants.\n")

# S2 variables
w("## Table S2 Predictors, NHANES variables and harmonization\n")
w("| Block | Predictor | NHANES variable(s) (2017–Mar 2020 file / 2021–2023 file) | Coding |\n|---|---|---|---|")
rows = [
    ("Core", "Age", "RIDAGEYR (P_DEMO / DEMO_L)", "Years; top-coded at 80"),
    ("Core", "Sex", "RIAGENDR", "Male/female"),
    ("Core", "Race and ethnicity", "RIDRETH3", "6 categories, one-hot"),
    ("B1", "Weight, height, BMI, waist", "BMXWT, BMXHT, BMXBMI, BMXWAIST (P_BMX / BMX_L)", "Measured; continuous"),
    ("B1", "Waist-to-height ratio", "BMXWAIST / BMXHT", "Derived per participant"),
    ("B2", "Systolic and diastolic BP", "BPXOSY1–3, BPXODI1–3 (P_BPXO / BPXO_L)", "Mean of available oscillometric readings"),
    ("B3", "Ever told high blood pressure", "BPQ020 (P_BPQ / BPQ_L)", "Yes/no; 7, 9 set to missing"),
    ("B4", "Smoking status", "SMQ020, SMQ040 (P_SMQ / SMQ_L)", "Never / former / current"),
    ("B4", "Daily sitting time", "PAD680 (P_PAQ / PAQ_L)", "Minutes; 7777, 9999 set to missing"),
    ("B4", "Income-to-poverty ratio", "INDFMPIR", "Continuous; top-coded at 5"),
    ("B4", "Education", "DMDEDUC2", "5 categories; 7, 9 set to missing"),
    ("Outcome", "HbA1c", "LBXGH (P_GHB / GHB_L)", "≥6.5% (primary); ≥5.7% (secondary)"),
    ("Weights", "HbA1c sample weight", "WTMECPRP (P_DEMO) / WTPH2YR (GHB_L)", "Survey weight for evaluation"),
    ("Design", "Pseudo-stratum, pseudo-PSU", "SDMVSTRA, SDMVPSU", "Cross-validation groups; JK2 replicates"),
    ("Post hoc", "Self-reported weight and height", "WHD020, WHD010 (P_WHQ / WHQ_L)", "7777 and 9999 set to missing first; then lb → kg, in → cm; BMI derived"),
]
for r in rows:
    w("| " + " | ".join(r) + " |")
w("\nNot used: family history of diabetes (MCQ300C) and gestational diabetes (RHQ162), not released in the 2021–2023 "
  "files; leisure-time physical activity (PAQ650/PAQ665 vs PAD790Q/PAD810Q), wording changed between cycles "
  "(57% vs 84% classified as active). Excluded to prevent leakage: DIQ160, DIQ180, BPQ080, lipid-lowering and "
  "glucose-lowering medication, all laboratory variables.\n")

# S3 missingness
w("## Table S3 Naturally missing values among included participants, %\n")
w("| Block | Variable | 2017–Mar 2020 | 2021–2023 |\n|---|---|---|---|")
keep = ["RIDAGEYR", "RIAGENDR", "RIDRETH3", "BMXWT", "BMXHT", "BMXBMI", "BMXWAIST", "BPXOSY1", "BPXODI1", "BPQ020",
        "SMQ020", "SMQ040", "PAD680", "INDFMPIR", "DMDEDUC2"]
for v in keep:
    r = miss[miss["var"] == v]
    p = r[r.cycle == "P"].pct_missing.iat[0]
    l_ = r[r.cycle == "L"].pct_missing.iat[0]
    w(f"| {r.block.iat[0]} | {v} | {p:.1f} | {l_:.1f} |")
import sys
sys.path.insert(0, str(ROOT / "src"))
import final_pipeline as fp
import nhanes_audit as na
def _sr(c, cyc):
    q = na.read_xpt(ROOT / "data" / "raw" / ("P_WHQ.xpt" if cyc == "P" else "WHQ_L.xpt"))[["SEQN", "WHD010", "WHD020"]]
    for v in ["WHD010", "WHD020"]:
        q[v] = q[v].where(~q[v].isin([7777, 9999]))
    c = c.merge(q, on="SEQN", how="left")
    c["SR_BMI"] = (c["WHD020"] * 0.4536) / ((c["WHD010"] * 2.54) / 100) ** 2
    return c
_c = {k: _sr(fp.cohort(k, ROOT / "data" / "raw", 6.5), k) for k in "PL"}
for v, lab in [("SMOKE3", "Smoking status (derived)"), ("SBP_MEAN", "Mean systolic BP (derived)"),
               ("DBP_MEAN", "Mean diastolic BP (derived)"), ("WHTR", "Waist-to-height ratio (derived)"),
               ("WHD020", "Self-reported weight (post hoc)"), ("WHD010", "Self-reported height (post hoc)"),
               ("SR_BMI", "Self-reported BMI (post hoc)")]:
    w(f"| derived | {lab} | {_c['P'][v].isna().mean()*100:.1f} | {_c['L'][v].isna().mean()*100:.1f} |")
w("\nSMQ040 is asked only of participants who had smoked at least 100 cigarettes; the derived smoking status is "
  "missing only when SMQ020 is missing.\n")

# S4 hyperparameters
c = cfg["config"]["LR"]
w("## Table S4 Final model settings (development data)\n")
w("| Item | Value |\n|---|---|")
w("| Learner | L2-penalized logistic regression (scikit-learn 1.7.2, lbfgs, max_iter 5000) |")
w("| Continuous predictors | Median imputation with missing-value indicators; cubic B-splines, 4 knots uniformly spaced "
  "over the training range (SplineTransformer defaults) |")
w("| Categorical predictors | Most-frequent imputation; one-hot encoding |")
w(f"| C (inverse penalty), M-BASE | {c['BASE']} |")
w(f"| C, M-AUG (each of 5 seeds) | {c['AUG']} |")
w("| C, M-PS submodels S0 / S1 / S2 / S3 / S4 / S5 / S6 | " + " / ".join(str(c['PS'][k]) for k in
                                                                        ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6']) + " |")
w("| Augmentation | 1 masked copy per record; scenario drawn uniformly from S1–S5; 4 block indicators; seeds 0–4 |")
th = cfg["thresholds"]
w(f"| Decision thresholds (80% sensitivity, development OOF) | M-AUG {th['LR-AUG']:.4f}; M-PS {th['LR-PS']:.4f}; "
  f"M-BASE {th['LR-BASE']:.4f} |")
rc = cfg["recal"]
w(f"| Logistic recalibration (a, b) | M-AUG ({rc['LR-AUG'][0]:.3f}, {rc['LR-AUG'][1]:.3f}); "
  f"M-PS ({rc['LR-PS'][0]:.3f}, {rc['LR-PS'][1]:.3f}) |")
g = cfg["config"]["LGB"]
w(f"| LightGBM (secondary), 300 trees | M-BASE {g['BASE']}; M-AUG {g['AUG']}; grid: num_leaves {{7, 15, 31}} × "
  "min_child_samples {20, 50} × learning_rate {0.05, 0.1} |")
w("| LightGBM M-PS submodels S0–S6 | " + "; ".join(f"{k}: {v}" for k, v in g["PS"].items()) + " |")
w("| Full configuration file | final_out/config_P.json in the repository |")
w("| Tuning criterion | Survey-weighted log loss, 5-fold GroupKFold by pseudo-stratum × pseudo-PSU |\n")

# S5 Bang
w("## Table S5 Bang self-assessment score as implemented\n")
w("| Item | Points | Implementation |\n|---|---|---|")
for r in [("Age <40 / 40–49 / 50–59 / ≥60 years", "0 / 1 / 2 / 3", "RIDAGEYR"),
          ("Male sex", "1", "RIAGENDR"),
          ("Family history of diabetes", "1", "Not available in 2021–2023; scored 0 for all"),
          ("History of hypertension", "1", "BPQ020 = yes, or mean measured systolic BP ≥140 or mean diastolic BP ≥90 mmHg (mean of available oscillometric readings). Antihypertensive medication (BPQ040A / BPQ150) is asked only when BPQ020 = yes, so adding it changed no score (0 participants in either cycle)"),
          ("Overweight / obese / extremely obese", "1 / 2 / 3",
           "BMI 25–<30 / 30–<40 / ≥40, or waist (inches) 37–<40 / 40–<50 / ≥50 (men), 31.5–<35 / 35–<49 / ≥49 (women); when BMI and waist fall in different categories, the higher category is scored"),
          ("Physically active", "−1", "Original question not asked; scored 0 for all"),
          ("Cut-off", "≥5 (undiagnosed diabetes); ≥4 (prediabetes or diabetes)", "As published")]:
    w("| " + " | ".join(r) + " |")
w("\nMissing inputs were scored as 0 for the corresponding item, following the instruction of the score for unknown answers: in 2021–2023, 48 participants lacked both BMI and waist circumference (obesity item 0) and 104 lacked measured blood pressure and did not report hypertension (hypertension item 0).\n")

# S8 missingness indicators and pattern-submodel definition (clarifications requested by peer review)
w("## Section S3 Missingness indicators, pattern-submodel training, and scenario routing\n")
w('"Pattern submodels" (M-PS) here denotes a reduced-feature variant: for each scenario S0–S6, a submodel was '
  "fitted on the same full development sample used for M-AUG and M-BASE, with the columns of the blocks removed "
  "from the design matrix (`X_drop` in `src/final_pipeline.py`). This differs from the original pattern-submodel "
  "method of Mercaldo and Blume, which restricts training to the records that naturally exhibit each pattern and "
  "thereby obtains a guarantee under data not missing at random; the variant used here was compared empirically "
  "rather than assumed to carry that guarantee.\n\n"
  "The four block-level missingness indicators (MISS_B1–MISS_B4) used by M-AUG and M-BASE are set to 1 only for "
  "blocks that a scenario actively sets to missing (`X_mask` in `src/final_pipeline.py`); a participant who is "
  "naturally missing all variables in a retained block keeps indicator 0 for that block; that block's own missing "
  "values are handled by the per-variable median imputation and missing-value indicators inside the logistic-"
  "regression pipeline, not by the block-level indicator. This is a modelling choice, not an error: it lets the "
  "block indicators represent the deployment scenario being simulated rather than the union of simulated and "
  "naturally occurring missingness.\n\n"
  "In scenario S7 (Section 2.5), each of the 4,826 validation participants was independently assigned, with "
  "probability 0.5 (education ≤ high school) or 0.1 (otherwise), to have the lifestyle/socioeconomic block (B4) "
  "masked; 1,082 participants were masked in the realised draw (`03b_evaluate_L.py`). For M-AUG, every "
  "participant's prediction came from the same five-seed predictor, applied with B4 masked or intact according to "
  "that draw (`AugEnsemble.predict` with `row_mask`). For M-PS, each participant's prediction came from the S4 "
  "submodel if B4 was masked for them and from the S0 submodel otherwise (`PatternSub.predict` with `row_mask`); "
  "there is no single combined \"S7 model\", only this per-participant routing.\n")

# S6 seeds
w("## Table S6 Individual augmentation seeds (NHANES 2021–2023, post hoc)\n")
w("| Seed | Brier skill at S0 (95% CI) | Difference from M-PS, mean S1–S5 (95% CI) |\n|---|---|---|")
R1 = rev["R1_seeds"]
for s in range(5):
    a, d = R1[f"seed{s}_skill_S0"], R1[f"seed{s}_delta_vs_PS_S1_S5"]
    w(f"| {s} | {a['est']:.4f} ({a['lo']:.4f}, {a['hi']:.4f}) | {d['est']:.4f} ({d['lo']:.4f}, {d['hi']:.4f}) |")
w("\nThe reported M-AUG predictor averages the predicted probabilities of the five seeds. Point estimates were similar across seeds; for seed 1 the confidence interval extended slightly beyond the lower equivalence margin (−0.0053), so equivalence was not established for every seed individually.\n")

# S7 per-scenario equivalence
w("## Table S7 Scenario-specific differences, M-AUG − M-PS (Brier skill)\n")
w("| Scenario | Difference | 95% CI | Relative to ±0.005 margin |\n|---|---|---|---|")
lab = {"tương đương thực tế (CI trong ±δ)": "within margin", "không kết luận được": "crosses margin (inconclusive)"}
for k, v in rev["R4_per_scenario"].items():
    w(f"| {k} | {v['est']:.4f} | {v['lo']:.4f}, {v['hi']:.4f} | {lab.get(v['decision'], v['decision'])} |")
w("")

# S1 JK2
w("## Section S1 Jackknife (JK2) variance estimation\n")
w("The 2021–2023 design has 15 pseudo-strata, each with two pseudo-PSUs; after participant selection all 15 strata "
  "still contained participants in both pseudo-PSUs (checked by an assertion in the code). For stratum *h* "
  "(h = 1, …, 15), a replicate weight is formed by multiplying the sample weight by 2 for participants in the "
  "pseudo-PSU with the lower code (SDMVPSU = 1) and by 0 for those in the other pseudo-PSU, leaving all other strata "
  "unchanged (paired jackknife; Rust and Rao, Stat Methods Med Res 1996;5:283–310). Every quantity θ (Brier skill, AUROC, "
  "calibration measures, sensitivity, differences between methods) is recomputed with each replicate weight, "
  "including the weighted prevalence used in Brier~null~, giving θ~h~. The variance is "
  "Var(θ̂) = Σ~h~ (θ~h~ − θ̂)^2^, and the 95% confidence interval is θ̂ ± t~0.975,15~ √Var(θ̂). Differences "
  "between methods are computed within each replicate (paired). Models were fixed after development, so the "
  "intervals do not include model-fitting uncertainty.\n")

# S2 lock
w("## Section S2 Analysis plan lock and reproducibility\n")
w(f"The lock file (LOCK_protocol_v0.4.json) was created on {lock['created']} (local time, UTC+07:00) and records SHA-256 hashes of the "
  "protocol, decision log, source code, stage A/B scripts, trained models and configuration. The confirmatory "
  "analysis of the validation cycle specified in the plan (stage B) was run once on 2026-09-24, and the hash of the "
  "resulting prediction file is recorded in the post-lock log, which also lists all further analyses. The lock is internal to the project and is not an independent preregistration. Code, protocol "
  "versions (v0.2–v0.4), decision log, lock file, trained models, predictions and post-lock log are available at "
  "https://github.com/FresherCod/nhanes-hba1c-block-missingness.\n")
w("| Locked file | SHA-256 (full) |\n|---|---|")
for f, h in lock["files"].items():
    w(f"| {f} | `{h}` |")

OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
print("written", OUT)
