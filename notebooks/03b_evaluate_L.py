# Giai đoạn B — nạp L MỘT LẦN, sau khi khóa. Chạy từ thư mục gốc: python notebooks/03b_evaluate_L.py
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import final_pipeline as fp

import os

DRYRUN = os.environ.get("DRYRUN") == "1"  # kiểm tra code bằng dữ liệu P, KHÔNG nạp L
RAW, MODELS = ROOT / "data" / "raw", ROOT / "final_out"
OUT = MODELS / "dryrun_P" if DRYRUN else MODELS
OUT.mkdir(exist_ok=True)
LOCK = ROOT / "LOCK_protocol_v0.4.json"
PRED = OUT / "L_predictions.csv"

if not DRYRUN:
    # K10 + kiểm mã băm: mọi file đã khóa phải giữ nguyên
    if not LOCK.exists():
        raise PermissionError("Chưa khóa protocol")
    lock = fp.verify_lock(ROOT, LOCK)
    if PRED.exists():
        raise PermissionError("L đã được chạy một lần (L_predictions.csv tồn tại). Không chạy lại.")
t0 = time.time()
run_log = {"lock_created": None if DRYRUN else lock["created"], "dryrun": DRYRUN,
           "started": time.strftime("%Y-%m-%d %H:%M:%S")}

B = fp.load_pickle(MODELS / "models_P.pkl")
M, TH, RC = B["models"], B["thresholds"], B["recal"]
if DRYRUN:
    # P đóng vai L: giữ strata có đúng 2 PSU (JK2). Dự đoán trong mẫu → số liệu vô nghĩa, chỉ để test code.
    def _two_psu(c):
        k = c.groupby("SDMVSTRA")["SDMVPSU"].nunique()
        return c[c.SDMVSTRA.isin(k[k == 2].index)].reset_index(drop=True)
    L = _two_psu(fp.cohort("P", RAW, threshold=6.5))
    L57 = _two_psu(fp.cohort("P", RAW, threshold=5.7))
else:
    L = fp.cohort("L", RAW, threshold=6.5).reset_index(drop=True)
    L57 = fp.cohort("L", RAW, threshold=5.7).reset_index(drop=True)
print("L:", len(L), "sự kiện:", int(L.y.sum()), "| strata:", L.SDMVSTRA.nunique())

# ---- dự đoán (một lần), lưu kèm mã băm
rng7 = np.random.default_rng(fp.S7_PROB["seed"])
low_edu = (L["DMDEDUC2"] <= 3).values
s7_mask = rng7.random(len(L)) < np.where(low_edu, fp.S7_PROB["low_edu"], fp.S7_PROB["high_edu"])
preds = {}
for key in ["LR-BASE", "LR-AUG", "LR-PS", "LGB-BASE", "LGB-AUG", "LGB-PS", "LRw-AUG", "LRw-PS"]:
    for s, bl in fp.SCEN.items():
        preds[(key, s)] = M[key].predict(L, bl)
    preds[(key, "S7")] = M[key].predict(L, ["B4"], row_mask=s7_mask)
for key in ["LR57-BASE", "LR57-AUG", "LR57-PS"]:
    for s, bl in fp.SCEN.items():
        preds[(key, s)] = M[key].predict(L57, bl)
bang = fp.bang_score(L)
long = pd.DataFrame([{"SEQN": seqn, "model": k, "scenario": s, "p": v}
                     for (k, s), arr in preds.items() for seqn, v in zip(
                         (L57 if k.startswith("LR57") else L)["SEQN"].values, arr)])
long.to_csv(PRED, index=False)
run_log["pred_sha256"] = fp.sha(PRED)
run_log["s7_masked_n"] = int(s7_mask.sum())
print(f"Đã lưu dự đoán ({time.time()-t0:.0f}s)")


def P(key, s):
    return preds[(key, s)]


results = {}

# ---- ƯỚC LƯỢNG CHÍNH (LR): Δ skill AUG − PS, trung bình S1–S5; S0 không kém hơn
def primary(w, df=L, a="LR-AUG", b="LR-PS"):
    y = df.y.values
    d = [fp.metrics(y, P(a, s), w)["skill"] - fp.metrics(y, P(b, s), w)["skill"] for s in fp.PRIMARY]
    s0 = fp.metrics(y, P(a, "S0"), w)["skill"] - fp.metrics(y, P(b, "S0"), w)["skill"]
    out = {"delta_mean_S1_S5": float(np.mean(d)), "delta_S0": float(s0)}
    out.update({f"delta_{s}": float(v) for s, v in zip(fp.PRIMARY, d)})
    return out


prim = fp.with_ci(primary, L)
results["primary"] = prim
results["primary_decision"] = fp.decide(prim["delta_mean_S1_S5"])
results["S0_noninferior"] = bool(prim["delta_S0"]["lo"] > -fp.DELTA)
print("CHÍNH:", {k: round(v["est"], 4) for k, v in prim.items()}, results["primary_decision"],
      "| S0 không kém:", results["S0_noninferior"])


# ---- bảng chỉ số theo mô hình × kịch bản (có CI)
def table(keys, scen, df=L, thr_key=lambda k: k):
    rows = []
    for k in keys:
        for s in scen:
            thr = TH.get(thr_key(k))
            ci = fp.with_ci(lambda w: fp.metrics(df.y.values, P(k, s), w, thr), df)
            rows.append({"model": k, "scenario": s,
                         **{f"{m}": v["est"] for m, v in ci.items()},
                         **{f"{m}_lo": v["lo"] for m, v in ci.items()},
                         **{f"{m}_hi": v["hi"] for m, v in ci.items()}})
    return pd.DataFrame(rows)


scen_all = list(fp.SCEN) + ["S7"]
tab = table(["LR-AUG", "LR-PS", "LR-BASE"], scen_all)
tab.to_csv(OUT / "L_table_LR.csv", index=False)
tab_lgb = table(["LGB-AUG", "LGB-PS", "LGB-BASE"], scen_all)
tab_lgb.to_csv(OUT / "L_table_LGB.csv", index=False)
tab_w = table(["LRw-AUG", "LRw-PS"], list(fp.SCEN), thr_key=lambda k: k.replace("LRw", "LR"))
tab_w.to_csv(OUT / "L_table_LR_weighted_training.csv", index=False)
print(f"Bảng chính xong ({time.time()-t0:.0f}s)")


# ---- phụ: so sánh ghép cặp khác
def pair(a, b, scen_list=fp.PRIMARY, df=L):
    return fp.with_ci(lambda w: {"delta": float(np.mean(
        [fp.metrics(df.y.values, P(a, s), w)["skill"] - fp.metrics(df.y.values, P(b, s), w)["skill"]
         for s in scen_list]))}, df)["delta"]


def degr(k, df=L):
    return fp.with_ci(lambda w: {"d": float(
        fp.metrics(df.y.values, P(k, "S0"), w)["skill"] - np.mean(
            [fp.metrics(df.y.values, P(k, s), w)["skill"] for s in fp.PRIMARY]))}, df)["d"]


sec = {
    "LR AUG−BASE (S1–S5)": pair("LR-AUG", "LR-BASE"),
    "LR PS−BASE (S1–S5)": pair("LR-PS", "LR-BASE"),
    "LR BASE mất skill khi thiếu (S0 − S1…S5)": degr("LR-BASE"),
    "LR AUG−PS tại S6 (không dùng khi huấn luyện AUG)": pair("LR-AUG", "LR-PS", ["S6"]),
    "LR AUG−PS tại S7 (MAR)": pair("LR-AUG", "LR-PS", ["S7"]),
    "LGB AUG−PS (S1–S5)": pair("LGB-AUG", "LGB-PS"),
    "LRw AUG−PS (S1–S5), huấn luyện có trọng số": pair("LRw-AUG", "LRw-PS"),
    "LR-AUG − LGB-AUG (S1–S5)": pair("LR-AUG", "LGB-AUG"),
}

# nhãn thay thế (6,4 / 6,7) và loại borderline — cùng dự đoán
for thr in (6.4, 6.7):
    Lt = L.copy(); Lt["y"] = (Lt["LBXGH"] >= thr).astype(int)
    sec[f"LR AUG−PS (S1–S5), nhãn ≥{thr}"] = fp.with_ci(lambda w: primary(w, Lt), Lt)["delta_mean_S1_S5"]
    sec[f"sự kiện nhãn ≥{thr}"] = {"est": int(Lt.y.sum())}
nb = (L["DIQ010"] != 3).values
Lb = L[nb].reset_index(drop=True)
_saved = dict(preds)
preds = {k: v[nb] if len(v) == len(L) and not k[0].startswith("LR57") else v for k, v in _saved.items()}
sec["LR AUG−PS (S1–S5), loại borderline"] = fp.with_ci(lambda w: primary(w, Lb), Lb)["delta_mean_S1_S5"]
preds = _saved

# nhãn 5,7 (mô hình riêng)
sec["LR57 AUG−PS (S1–S5), nhãn ≥5,7"] = pair("LR57-AUG", "LR57-PS", df=L57)
results["secondary"] = sec
tab57 = table(["LR57-AUG", "LR57-PS", "LR57-BASE"], list(fp.SCEN), df=L57, thr_key=lambda k: None)
tab57.to_csv(OUT / "L_table_LR_label57.csv", index=False)

# Hiệu chuẩn lại (logistic fit trên OOF P) cho LR tại S0 và S1–S5
rows = []
for k in ["LR-AUG", "LR-PS", "LR-BASE"]:
    for s in ["S0"] + fp.PRIMARY:
        pr = fp.apply_recal(RC[k], P(k, s))
        ci = fp.with_ci(lambda w: fp.metrics(L.y.values, pr, w), L)
        rows.append({"model": k + "+recal", "scenario": s, **{m: v["est"] for m, v in ci.items()},
                     **{f"{m}_lo": v["lo"] for m, v in ci.items()}, **{f"{m}_hi": v["hi"] for m, v in ci.items()}})
pd.DataFrame(rows).to_csv(OUT / "L_table_LR_recalibrated.csv", index=False)

# Điểm Bang (≥5), S0
from sklearn.metrics import roc_auc_score
def bang_fn(w):
    y = L.y.values; pos = bang >= 5; W = w.sum()
    tp, fp_ = np.sum(w * pos * (y == 1)), np.sum(w * pos * (y == 0))
    fn, tn = np.sum(w * ~pos * (y == 1)), np.sum(w * ~pos * (y == 0))
    return {"auc": roc_auc_score(y, bang, sample_weight=w), "sens": tp / (tp + fn),
            "spec": tn / (tn + fp_), "ppv": tp / (tp + fp_), "referral": (tp + fp_) / W}
results["bang"] = fp.with_ci(bang_fn, L)

# Phân nhóm (chỉ nhóm ≥30 sự kiện)
sub_rows = []
L["AGEGRP"] = pd.cut(L.RIDAGEYR, [19, 44, 64, 200], labels=["20-44", "45-64", "65+"])
L["PIRGRP"] = pd.cut(L.INDFMPIR, [-1, 1.3, 3.5, 10], labels=["<1.3", "1.3-3.5", ">3.5"])
for g in ["AGEGRP", "RIAGENDR", "RIDRETH3", "PIRGRP"]:
    for lvl in L[g].dropna().unique():
        m = (L[g] == lvl).values
        ev = int(L.y.values[m].sum())
        row = {"group": g, "level": str(lvl), "n": int(m.sum()), "events": ev}
        if ev >= 30:
            for k in ["LR-AUG", "LR-PS"]:
                for s in ["S0"]:
                    r = fp.metrics(L.y.values[m], P(k, s)[m], L.w.values[m])
                    row[f"{k}_{s}_skill"], row[f"{k}_{s}_auc"] = r["skill"], r["auc"]
                row[f"{k}_S1-5_skill"] = float(np.mean([fp.metrics(L.y.values[m], P(k, s)[m],
                                                                   L.w.values[m])["skill"] for s in fp.PRIMARY]))
        sub_rows.append(row)
pd.DataFrame(sub_rows).to_csv(OUT / "L_subgroups_descriptive.csv", index=False)

run_log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
run_log["seconds"] = round(time.time() - t0)
results["run_log"] = run_log
(OUT / "L_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str),
                                    encoding="utf-8")
print("PHỤ:")
for k, v in sec.items():
    print(" ", k, {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()
                   if kk in ("est", "lo", "hi")})
print("BANG:", {k: round(v["est"], 3) for k, v in results["bang"].items()})
print(f"Hoàn tất ({run_log['seconds']}s)")
