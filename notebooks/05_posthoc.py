# HẬU KIỂM (post hoc) — sau khi protocol v0.4 đã khóa và L đã chạy một lần.
# Không sửa file đã khóa. Mọi kết quả ở đây phải được gắn nhãn "hậu kiểm" trong bài.
# PH-1: vai trò khối nhân trắc (tách mức mất skill; kịch bản thiếu thước dây và cân/đo tự khai)
# PH-2: nhãn HbA1c ≥5,7% (ngưỡng, so với điểm Bang ≥4, net benefit)
# Chạy từ thư mục gốc: python notebooks/05_posthoc.py
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
OUT.mkdir(exist_ok=True)
B = fp.load_pickle(ROOT / "final_out" / "models_P.pkl")
pred = pd.read_csv(ROOT / "final_out" / "L_predictions.csv")
res = {"label": "HẬU KIỂM — không thuộc protocol v0.4"}


def get(model, scen, seqn):
    d = pred[(pred.model == model) & (pred.scenario == scen)].set_index("SEQN")["p"]
    return d.loc[seqn].values


def add_selfreport(coh: pd.DataFrame, cycle: str) -> pd.DataFrame:
    w = na.read_xpt(RAW / ("P_WHQ.xpt" if cycle == "P" else "WHQ_L.xpt"))[["SEQN", "WHD010", "WHD020"]]
    for v in ["WHD010", "WHD020"]:
        w[v] = w[v].where(~w[v].isin([7777, 9999]))
    c = coh.merge(w, on="SEQN", how="left")
    c["SR_HT"] = c["WHD010"] * 2.54        # inch → cm
    c["SR_WT"] = c["WHD020"] * 0.4536      # lb → kg
    c["SR_BMI"] = c["SR_WT"] / (c["SR_HT"] / 100) ** 2
    return c


def oof_tune_fit(P: pd.DataFrame, cols: list[str]):
    """Cùng quy trình định trước: lưới C, chọn theo log loss có trọng số trên OOF GroupKFold theo PSU."""
    y, w = P["y"].values, P["w"].values
    best = None
    for C in fp.C_GRID:
        o = np.full(len(P), np.nan)
        for tr, va in GroupKFold(5).split(P, y, P["grp"]):
            m = fp.lr_model(cols, C).fit(P.iloc[tr][cols], y[tr])
            o[va] = m.predict_proba(P.iloc[va][cols])[:, 1]
        ll = fp.wlogloss(y, o, w)
        if best is None or ll < best[0]:
            best = (ll, C, o)
    _, C, o = best
    return fp.lr_model(cols, C).fit(P[cols], y), C, o


# =====================================================================================
# PH-1a: tách mức mất skill theo khối (dự đoán đã lưu, không huấn luyện lại)
L = fp.cohort("L", RAW, 6.5).reset_index(drop=True)
seq = L["SEQN"].values


def block_loss(w):
    out = {}
    for mdl in ["LR-AUG", "LR-PS"]:
        s0 = fp.metrics(L.y.values, get(mdl, "S0", seq), w)["skill"]
        loss = {s: s0 - fp.metrics(L.y.values, get(mdl, s, seq), w)["skill"] for s in ["S1", "S2", "S3", "S4"]}
        for s, v in loss.items():
            out[f"{mdl}_loss_{s}"] = v
        out[f"{mdl}_loss_B1_minus_meanB2B4"] = loss["S1"] - np.mean([loss["S2"], loss["S3"], loss["S4"]])
        out[f"{mdl}_share_B1_of_S0skill"] = loss["S1"] / s0
    return out


res["PH1a_block_loss"] = fp.with_ci(block_loss, L)

# =====================================================================================
# PH-1b: thiếu một phần nhân trắc — mô hình con mới (LR, cùng quy trình tuning), trên P → L
P = add_selfreport(fp.cohort("P", RAW, 6.5), "P")
Ls = add_selfreport(L, "L")
base_cols = fp.keep_cols(["B1"])                       # không nhân trắc
A1 = base_cols + ["BMXWT", "BMXHT", "BMXBMI"]         # có cân + thước đo cao, KHÔNG có thước dây
A2 = base_cols + ["SR_WT", "SR_HT", "SR_BMI"]         # chỉ cân/đo tự khai
fp.NUM.extend([c for c in ["SR_WT", "SR_HT", "SR_BMI"] if c not in fp.NUM])  # để lr_model coi là biến liên tục
ph1b = {}
for name, cols in {"A1_no_tape": A1, "A2_self_report": A2}.items():
    m, C, _ = oof_tune_fit(P, cols)
    ph1b[name] = {"C": C, "p": m.predict_proba(Ls[cols])[:, 1]}
res["PH1b_C"] = {k: v["C"] for k, v in ph1b.items()}
res["PH1b_selfreport_missing_L"] = {v: float(Ls[v].isna().mean()) for v in ["SR_WT", "SR_HT"]}
res["PH1b_corr_measured_selfreport_BMI_L"] = float(Ls[["BMXBMI", "SR_BMI"]].corr().iloc[0, 1])


def ph1b_fn(w):
    y = Ls.y.values
    sk = {"S0_full": fp.metrics(y, get("LR-PS", "S0", seq), w)["skill"],
          "S1_no_anthro": fp.metrics(y, get("LR-PS", "S1", seq), w)["skill"],
          "A1_no_tape": fp.metrics(y, ph1b["A1_no_tape"]["p"], w)["skill"],
          "A2_self_report": fp.metrics(y, ph1b["A2_self_report"]["p"], w)["skill"]}
    out = {f"skill_{k}": v for k, v in sk.items()}
    for k in ["A1_no_tape", "A2_self_report"]:
        out[f"gain_{k}_vs_S1"] = sk[k] - sk["S1_no_anthro"]
        out[f"gap_S0_minus_{k}"] = sk["S0_full"] - sk[k]
        out[f"recovered_frac_{k}"] = (sk[k] - sk["S1_no_anthro"]) / (sk["S0_full"] - sk["S1_no_anthro"])
    for k, p in {"S0_full": get("LR-PS", "S0", seq), "S1_no_anthro": get("LR-PS", "S1", seq),
                 "A1_no_tape": ph1b["A1_no_tape"]["p"], "A2_self_report": ph1b["A2_self_report"]["p"]}.items():
        out[f"auc_{k}"] = roc_auc_score(y, p, sample_weight=w)
    return out


res["PH1b"] = fp.with_ci(ph1b_fn, Ls)

# =====================================================================================
# PH-2: nhãn ≥5,7 — ngưỡng (OOF P, độ nhạy 80%), so với điểm Bang ≥4 và ≥5, net benefit
P57 = fp.cohort("P", RAW, 5.7)
L57 = fp.cohort("L", RAW, 5.7).reset_index(drop=True)
seq57 = L57["SEQN"].values
cfg57 = B["config"]["LR57"]
thr57 = {}
for meth in ["AUG", "PS"]:
    o = fp.oof(P57, "LR", meth, cfg57[meth] if meth == "AUG" else cfg57["PS"]["S0"],
               ["S0"], s_ps="S0" if meth == "PS" else None)["S0"]
    thr57[meth] = fp.sens_threshold(P57.y.values, o, P57.w.values)
res["PH2_thresholds_from_P"] = thr57
bang57 = fp.bang_score(L57)
NB_T = [0.1, 0.2, 0.3, 0.4, 0.5]


def nb(y, pos, w, t):
    W = w.sum()
    return np.sum(w * pos * (y == 1)) / W - np.sum(w * pos * (y == 0)) / W * t / (1 - t)


def ph2_fn(w):
    y = L57.y.values
    out = {}
    for meth in ["AUG", "PS", "BASE"]:
        for s in ["S0", "S1"]:
            p = get(f"LR57-{meth}", s, seq57)
            m = fp.metrics(y, p, w, thr57.get(meth))
            out[f"{meth}_{s}_skill"], out[f"{meth}_{s}_auc"] = m["skill"], m["auc"]
            if meth in thr57:
                for k in ["sens", "spec", "ppv", "npv", "referral"]:
                    out[f"{meth}_{s}_{k}"] = m[k]
            for t in NB_T:
                out[f"{meth}_{s}_nb{t}"] = nb(y, p >= t, w, t)
    out["BASE_loss_S0_minus_S1"] = out["BASE_S0_skill"] - out["BASE_S1_skill"]
    out["AUG_minus_BASE_S1"] = out["AUG_S1_skill"] - out["BASE_S1_skill"]
    out["bang_auc"] = roc_auc_score(y, bang57, sample_weight=w)
    for cut in (4, 5):
        pos = bang57 >= cut
        W = w.sum()
        tp, fp_ = np.sum(w * pos * (y == 1)), np.sum(w * pos * (y == 0))
        fn, tn = np.sum(w * ~pos * (y == 1)), np.sum(w * ~pos * (y == 0))
        out.update({f"bang{cut}_sens": tp / (tp + fn), f"bang{cut}_spec": tn / (tn + fp_),
                    f"bang{cut}_ppv": tp / (tp + fp_), f"bang{cut}_referral": (tp + fp_) / W})
        for t in NB_T:
            out[f"bang{cut}_nb{t}"] = nb(y, pos, w, t)
    for t in NB_T:
        out[f"all_nb{t}"] = nb(y, np.ones(len(y), bool), w, t)
        out[f"AUG_S0_minus_bang4_nb{t}"] = out[f"AUG_S0_nb{t}"] - out[f"bang4_nb{t}"]
    # so sánh ghép cặp tại độ nhạy tương đương: đặt ngưỡng mô hình sao cho tỷ lệ chuyển = Bang ≥4
    pA = get("LR57-AUG", "S0", seq57)
    ref = np.sum(w * (bang57 >= 4)) / w.sum()
    order = np.argsort(-pA); cw = np.cumsum(w[order]) / w.sum()
    t_eq = pA[order][np.searchsorted(cw, ref)]
    posA = pA >= t_eq
    out["AUG_at_bang4_referral_sens"] = np.sum(w * posA * (y == 1)) / np.sum(w * (y == 1))
    out["AUG_minus_bang4_sens_same_referral"] = out["AUG_at_bang4_referral_sens"] - out["bang4_sens"]
    out["prev_L_5.7"] = np.average(y, weights=w)
    return {k: float(v) for k, v in out.items()}


res["PH2"] = fp.with_ci(ph2_fn, L57)
res["PH2_n_events_L"] = int(L57.y.sum())

# dữ liệu cho hình DCA (ước lượng điểm, dải ngưỡng dày)
ts = np.round(np.arange(0.05, 0.71, 0.01), 2)
y57, w57 = L57.y.values, L57.w.values
dca = pd.DataFrame({"t": ts,
                    "LR57-AUG S0": [nb(y57, get("LR57-AUG", "S0", seq57) >= t, w57, t) for t in ts],
                    "LR57-AUG S1": [nb(y57, get("LR57-AUG", "S1", seq57) >= t, w57, t) for t in ts],
                    "Bang ≥4": [nb(y57, bang57 >= 4, w57, t) for t in ts],
                    "Xét nghiệm tất cả": [nb(y57, np.ones(len(y57), bool), w57, t) for t in ts]})
dca.to_csv(OUT / "PH2_dca.csv", index=False)
pd.DataFrame({"SEQN": Ls.SEQN, "y": Ls.y, "w": Ls.w, "A1_no_tape": ph1b["A1_no_tape"]["p"],
              "A2_self_report": ph1b["A2_self_report"]["p"]}).to_csv(OUT / "PH1b_L_predictions.csv", index=False)
(OUT / "posthoc_results.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str),
                                          encoding="utf-8")


def show(block):
    for k, v in block.items():
        print(f"  {k:42s} {v['est']:8.4f} [{v['lo']:8.4f}; {v['hi']:8.4f}]")


print("PH-1a"); show(res["PH1a_block_loss"])
print("PH-1b C:", res["PH1b_C"], "| thiếu tự khai:", res["PH1b_selfreport_missing_L"],
      "| r(BMI đo, BMI tự khai) =", round(res["PH1b_corr_measured_selfreport_BMI_L"], 3))
show(res["PH1b"])
print("PH-2 ngưỡng:", thr57, "| sự kiện L:", res["PH2_n_events_L"]); show(res["PH2"])
