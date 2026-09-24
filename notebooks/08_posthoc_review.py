# HẬU KIỂM đợt 2 — trả lời phản biện (sau khóa protocol v0.4). Không sửa file đã khóa.
# R1: độ biến thiên giữa 5 seed của M-AUG và Δ(M-AUG 1 seed − M-PS)
# R2: ΔAUROC ghép cặp M-AUG − điểm Bang (6,5% và 5,7%) với CI JK2
# R3: mô hình con "chỉ bảng hỏi" thật sự: lõi + B3 + B4 + cân/cao tự khai, KHÔNG huyết áp đo
# R4: tương đương theo từng kịch bản (CI so với ±δ)
# Chạy từ thư mục gốc: python notebooks/08_posthoc_review.py
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
import final_pipeline as fp
import nhanes_audit as na

RAW, OUT = ROOT / "data" / "raw", ROOT / "posthoc_out"
B = fp.load_pickle(ROOT / "final_out" / "models_P.pkl")
res = {"label": "HẬU KIỂM đợt 2 (phản biện) — không thuộc protocol v0.4"}
L = fp.cohort("L", RAW, 6.5).reset_index(drop=True)
L57 = fp.cohort("L", RAW, 5.7).reset_index(drop=True)
y = L.y.values

# ---- R1: từng seed của M-AUG (LR)
aug, ps = B["models"]["LR-AUG"], B["models"]["LR-PS"]
seed_pred = {s: {k: fp.predict("LR", m, fp.X_mask(L, bl)) for k, bl in fp.SCEN.items()}
             for s, m in zip(fp.AUG_SEEDS, aug.models)}
ps_pred = {k: ps.predict_s(L, k) for k in fp.SCEN}


def r1(w):
    out = {}
    for s, pr in seed_pred.items():
        sk = [fp.metrics(y, pr[k], w)["skill"] - fp.metrics(y, ps_pred[k], w)["skill"] for k in fp.PRIMARY]
        out[f"seed{s}_delta_vs_PS_S1_S5"] = float(np.mean(sk))
        out[f"seed{s}_skill_S0"] = fp.metrics(y, pr["S0"], w)["skill"]
    return out


res["R1_seeds"] = fp.with_ci(r1, L)

# ---- R2: ΔAUROC ghép cặp M-AUG − Bang
bang65, bang57 = fp.bang_score(L), fp.bang_score(L57)
pA65 = aug.predict(L, [])
pA57 = {s: B["models"]["LR57-AUG"].predict(L57, fp.SCEN[s]) for s in ["S0", "S1"]}


def r2a(w):
    return {"dAUC_65_S0": roc_auc_score(y, pA65, sample_weight=w) - roc_auc_score(y, bang65, sample_weight=w)}


def r2b(w):
    y57 = L57.y.values
    b = roc_auc_score(y57, bang57, sample_weight=w)
    return {"dAUC_57_S0": roc_auc_score(y57, pA57["S0"], sample_weight=w) - b,
            "dAUC_57_S1_vs_BangS0": roc_auc_score(y57, pA57["S1"], sample_weight=w) - b}


res["R2_dAUC_65"] = fp.with_ci(r2a, L)
res["R2_dAUC_57"] = fp.with_ci(r2b, L57)

# ---- R3: chỉ bảng hỏi (không đo gì): lõi + B3 + B4 + cân/cao tự khai
def add_sr(c, cyc):
    w = na.read_xpt(RAW / ("P_WHQ.xpt" if cyc == "P" else "WHQ_L.xpt"))[["SEQN", "WHD010", "WHD020"]]
    for v in ["WHD010", "WHD020"]:
        w[v] = w[v].where(~w[v].isin([7777, 9999]))
    c = c.merge(w, on="SEQN", how="left")
    c["SR_HT"], c["SR_WT"] = c["WHD010"] * 2.54, c["WHD020"] * 0.4536
    c["SR_BMI"] = c["SR_WT"] / (c["SR_HT"] / 100) ** 2
    return c


P = add_sr(fp.cohort("P", RAW, 6.5), "P")
Ls = add_sr(L, "L")
fp.NUM.extend([v for v in ["SR_WT", "SR_HT", "SR_BMI"] if v not in fp.NUM])
Q = fp.CORE + fp.BLOCKS["B3"] + fp.BLOCKS["B4"] + ["SR_WT", "SR_HT", "SR_BMI"]
Q0 = fp.CORE + fp.BLOCKS["B3"] + fp.BLOCKS["B4"]  # bảng hỏi, không có nhân trắc
assert not set(Q) & set(fp.BLOCKS["B1"] + fp.BLOCKS["B2"]), "R3: lẫn biến đo"


def tune_fit(cols):
    yP, wP = P.y.values, P.w.values
    best = None
    for C in fp.C_GRID:
        o = np.full(len(P), np.nan)
        for tr, va in GroupKFold(5).split(P, yP, P.grp):
            o[va] = fp.lr_model(cols, C).fit(P.iloc[tr][cols], yP[tr]).predict_proba(P.iloc[va][cols])[:, 1]
        ll = fp.wlogloss(yP, o, wP)
        if best is None or ll < best[0]:
            best = (ll, C)
    return fp.lr_model(cols, best[1]).fit(P[cols], yP), best[1]


mQ, cQ = tune_fit(Q)
mQ0, cQ0 = tune_fit(Q0)
pQ, pQ0 = mQ.predict_proba(Ls[Q])[:, 1], mQ0.predict_proba(Ls[Q0])[:, 1]
res["R3_C"] = {"questionnaire_selfreport": cQ, "questionnaire_no_anthro": cQ0}


def r3(w):
    full = fp.metrics(y, ps_pred["S0"], w)
    q = fp.metrics(y, pQ, w)
    q0 = fp.metrics(y, pQ0, w)
    return {"skill_full_measured": full["skill"], "auc_full_measured": full["auc"],
            "skill_questionnaire_selfreport": q["skill"], "auc_questionnaire_selfreport": q["auc"],
            "skill_questionnaire_no_anthro": q0["skill"], "auc_questionnaire_no_anthro": q0["auc"],
            "gap_full_minus_q_sr": full["skill"] - q["skill"],
            "gain_q_sr_minus_q0": q["skill"] - q0["skill"]}


res["R3_questionnaire_only"] = fp.with_ci(r3, Ls)

# ---- R4: tương đương theo từng kịch bản (từ kết quả đã khóa)
r = json.loads((ROOT / "final_out" / "L_results.json").read_text(encoding="utf-8"))
rows = {k: r["primary"][f"delta_{k}"] for k in fp.PRIMARY}
rows["S6"] = r["secondary"]["LR AUG−PS tại S6 (không dùng khi huấn luyện AUG)"]
rows["S7"] = r["secondary"]["LR AUG−PS tại S7 (MAR)"]
res["R4_per_scenario"] = {k: {"est": v["est"], "lo": v["lo"], "hi": v["hi"], "decision": fp.decide(v)}
                          for k, v in rows.items()}

(OUT / "posthoc_review_results.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str),
                                                 encoding="utf-8")


def show(b):
    for k, v in b.items():
        print(f"  {k:36s} {v['est']:8.4f} [{v['lo']:8.4f}; {v['hi']:8.4f}]")


print("R1"); show(res["R1_seeds"])
print("R2 6.5"); show(res["R2_dAUC_65"]); print("R2 5.7"); show(res["R2_dAUC_57"])
print("R3 C:", res["R3_C"]); show(res["R3_questionnaire_only"])
print("R4"); [print(" ", k, round(v["est"], 4), round(v["lo"], 4), round(v["hi"], 4), v["decision"]) for k, v in res["R4_per_scenario"].items()]
