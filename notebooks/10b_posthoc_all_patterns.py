# HẬU KIỂM đợt 3B (sau khóa protocol v0.4; xem addendum_posthoc_round3_20261014.md). Không sửa file đã khóa.
# Câu hỏi: khi xét ĐỦ 15 kiểu thiếu khối (2^4 - 1) thì "một mô hình" so với "nhiều mô hình con" ra sao?
#   M-AUG    : mô hình đã khóa (augmentation chỉ thấy S1-S5; 10 kiểu thiếu còn lại chưa từng thấy khi huấn luyện)
#   M-AUG15  : MỚI, huấn luyện chỉ trên P, augmentation bốc đều trong cả 15 kiểu thiếu
#   M-PS16   : MỚI, huấn luyện chỉ trên P, một mô hình con cho mỗi kiểu (đủ + 15 kiểu thiếu), cùng quy trình tuning như bản khóa
#   M-BASE   : mô hình đã khóa, để tham chiếu
# Mọi mô hình mới chỉ nhìn thấy P; L chỉ dùng để chấm điểm một lần cho mỗi mô hình. Không chọn gì trên L.
# Chạy từ thư mục gốc: python notebooks/10b_posthoc_all_patterns.py   (vài phút)
import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
import final_pipeline as fp

sys.stdout.reconfigure(encoding="utf-8")
RAW, OUT = ROOT / "data" / "raw", ROOT / "posthoc_out"
fp.verify_lock(ROOT, ROOT / "LOCK_protocol_v0.4.json")
print("LOCK OK")
t0 = time.time()

BL = list(fp.BLOCKS)  # B1..B4
PAT = {"S0": ()}
for r in range(1, len(BL) + 1):
    for c in itertools.combinations(BL, r):
        PAT["+".join(c)] = c
MISS = [k for k in PAT if k != "S0"]  # 15 kiểu thiếu
assert len(MISS) == 15
SEEN_LOCKED = {"B1", "B2", "B3", "B4", "B1+B2"}  # S1-S5 của bản khóa
NAMES_LOCKED = {"B1": "S1", "B2": "S2", "B3": "S3", "B4": "S4", "B1+B2": "S5", "B3+B4": "S6"}

P = fp.cohort("P", RAW, 6.5).reset_index(drop=True)
L = fp.cohort("L", RAW, 6.5).reset_index(drop=True)
yP, wP, yL = P.y.values, P.w.values, L.y.values
print(f"P n={len(P)} su kien={int(yP.sum())}; L n={len(L)} su kien={int(yL.sum())}")
B = fp.load_pickle(ROOT / "final_out" / "models_P.pkl")
aug_lock, base_lock, ps_lock = B["models"]["LR-AUG"], B["models"]["LR-BASE"], B["models"]["LR-PS"]


def augment_masks(X0, y, rng, masks):
    """Như fp.augment nhưng danh sách kiểu thiếu tuỳ chọn (mỗi dòng bốc đều một kiểu)."""
    pick = rng.integers(0, len(masks), size=len(X0))
    Xc = X0.copy()
    for i, bl in enumerate(masks):
        m = pick == i
        for b in bl:
            Xc.loc[m, fp.BLOCKS[b]] = np.nan
            Xc.loc[m, f"MISS_{b}"] = 1
    return pd.concat([X0, Xc], ignore_index=True), np.concatenate([y, y])


def fit_aug15(T, C):
    X0, y = fp.X_mask(T), T.y.values
    ms = []
    for s in fp.AUG_SEEDS:
        Xa, ya = augment_masks(X0, y, np.random.default_rng(s), [PAT[k] for k in MISS])
        ms.append(fp.fit_model("LR", C, Xa, ya, None, seed=s))
    return ms


def pred_aug15(ms, df, blocks):
    X = fp.X_mask(df, blocks)
    return np.mean([fp.predict("LR", m, X) for m in ms], axis=0)


# ---- M-PS16: tuning C theo từng kiểu, đúng quy trình bản khóa (OOF GroupKFold(5) theo PSU, log loss có trọng số, lưới C_GRID)
folds = list(GroupKFold(5).split(P, yP, P.grp))
C_PS = {}
for k, bl in PAT.items():
    best = None
    for C in fp.C_GRID:
        o = np.full(len(P), np.nan)
        for tr, va in folds:
            m = fp.fit_model("LR", C, fp.X_drop(P.iloc[tr], bl), yP[tr])
            o[va] = fp.predict("LR", m, fp.X_drop(P.iloc[va], bl))
        ll = fp.wlogloss(yP, o, wP)
        if best is None or ll < best[0]:
            best = (ll, C)
    C_PS[k] = best[1]
print("C chon cho M-PS16:", C_PS, f"({time.time()-t0:.0f}s)")
ps16 = {k: fp.fit_model("LR", C_PS[k], fp.X_drop(P, bl), yP) for k, bl in PAT.items()}

# ---- M-AUG15: tuning C theo log loss trung bình trên S0 + 15 kiểu thiếu (tương tự bản khóa: trung bình các kịch bản huấn luyện)
best = None
for C in fp.C_GRID:
    o = {k: np.full(len(P), np.nan) for k in PAT}
    for tr, va in folds:
        ms = fit_aug15(P.iloc[tr], C)
        for k, bl in PAT.items():
            o[k][va] = pred_aug15(ms, P.iloc[va], bl)
    ll = float(np.mean([fp.wlogloss(yP, o[k], wP) for k in PAT]))
    if best is None or ll < best[0]:
        best = (ll, C)
C_AUG15 = best[1]
print("C chon cho M-AUG15:", C_AUG15, f"({time.time()-t0:.0f}s)")
aug15 = fit_aug15(P, C_AUG15)

# ---- dự đoán trên L
pred = {"AUG": {}, "AUG15": {}, "PS16": {}, "BASE": {}}
for k, bl in PAT.items():
    pred["AUG"][k] = aug_lock.predict(L, list(bl))
    pred["BASE"][k] = base_lock.predict(L, list(bl))
    pred["AUG15"][k] = pred_aug15(aug15, L, bl)
    pred["PS16"][k] = fp.predict("LR", ps16[k], fp.X_drop(L, bl))


def skill(p, w):
    pb = np.average(yL, weights=w)
    return 1 - np.average((p - yL) ** 2, weights=w) / (pb * (1 - pb))


# ---- kiểm tra tái lập: M-PS16 phải trùng mô hình con đã khóa ở S0-S6, M-AUG/M-BASE phải trùng bảng đã khóa
w0 = L["w"].values
ref = pd.read_csv(ROOT / "final_out" / "L_table_LR.csv")
ref = {(r.model, r.scenario): r.skill for r in ref.itertuples()}
d_ps = [abs(skill(pred["PS16"][k], w0) - ref[("LR-PS", s)]) for k, s in NAMES_LOCKED.items()]
d_ps.append(abs(skill(pred["PS16"]["S0"], w0) - ref[("LR-PS", "S0")]))
d_aug = [abs(skill(pred["AUG"][k], w0) - ref[("LR-AUG", s)]) for k, s in NAMES_LOCKED.items() if s != "S6"]
print(f"Tai lap M-PS16 so voi M-PS da khoa (S0-S6): sai lech toi da = {max(d_ps):.2e}")
print(f"Tai lap M-AUG da khoa (S1-S5): sai lech toi da = {max(d_aug):.2e}")
assert max(d_aug) < 1e-9, "M-AUG khoa khong khop bang ket qua da khoa: DUNG"
if max(d_ps) > 1e-6:
    print("CANH BAO: M-PS16 khong trung hoan toan voi M-PS khoa (xem lai tuning/seed); ghi vao nhat ky truoc khi dien giai")

GROUPS = {"15 kieu": MISS,
          "co B1 (8)": [k for k in MISS if "B1" in k],
          "khong B1 (7)": [k for k in MISS if "B1" not in k],
          "da thay (S1-S5)": sorted(SEEN_LOCKED),
          "chua thay (10)": [k for k in MISS if k not in SEEN_LOCKED]}
VARS = {"AUG": "M-AUG(khoa)", "AUG15": "M-AUG15"}


def fn(w):
    sk = {(m, k): skill(pred[m][k], w) for m in pred for k in PAT}
    out = {f"skill_{m}_{k}": v for (m, k), v in sk.items()}
    for v in VARS:
        for k in MISS:
            out[f"{v}-PS16_{k}"] = sk[(v, k)] - sk[("PS16", k)]
        out[f"{v}-PS16_S0"] = sk[(v, "S0")] - sk[("PS16", "S0")]
        for g, ks in GROUPS.items():
            out[f"{v}-PS16_mean[{g}]"] = float(np.mean([sk[(v, k)] - sk[("PS16", k)] for k in ks]))
    out["PS16-BASE_mean[15 kieu]"] = float(np.mean([sk[("PS16", k)] - sk[("BASE", k)] for k in MISS]))
    return out


res = fp.with_ci(fn, L)
(OUT / "posthoc3b_all_patterns.json").write_text(json.dumps(
    {"label": "HAU KIEM dot 3B (15 kieu thieu) - khong thuoc protocol v0.4", "C_PS16": C_PS, "C_AUG15": C_AUG15,
     "results": res}, ensure_ascii=False, indent=2), encoding="utf-8")
rows = []
for k in ["S0"] + MISS:
    r = {"pattern": k, "locked_name": NAMES_LOCKED.get(k, ""), "seen_by_locked_AUG": k in SEEN_LOCKED or k == "S0"}
    for m in pred:
        r[f"skill_{m}"] = round(res[f"skill_{m}_{k}"]["est"], 4)
    for v in VARS:
        e = res[f"{v}-PS16_{k}"]
        r[f"{v}-PS16"] = round(e["est"], 4)
        r[f"{v}-PS16_lo"], r[f"{v}-PS16_hi"] = round(e["lo"], 4), round(e["hi"], 4)
        r[f"{v}-PS16_in_margin"] = bool(e["lo"] > -fp.DELTA and e["hi"] < fp.DELTA)
    rows.append(r)
pd.DataFrame(rows).to_csv(OUT / "posthoc3b_all_patterns.csv", index=False, encoding="utf-8")

pd.set_option("display.width", 250)
print("\nBrier skill (nhan >=6.5) va M-AUG - M-PS16 theo tung kieu thieu (CI JK2; margin +/-%.3f)" % fp.DELTA)
print(pd.DataFrame(rows).to_string(index=False))
print("\nTrung binh theo nhom kieu thieu (M-X - M-PS16)")
for v in VARS:
    for g in GROUPS:
        e = res[f"{v}-PS16_mean[{g}]"]
        print(f"  {VARS[v]:12s} {g:16s} {e['est']:8.4f} [{e['lo']:8.4f}; {e['hi']:8.4f}]")
e = res["PS16-BASE_mean[15 kieu]"]
print(f"  M-PS16 - M-BASE trung binh 15 kieu: {e['est']:.4f} [{e['lo']:.4f}; {e['hi']:.4f}]")
print(f"\nSo mo hinh: M-AUG = 5 (trung binh seed), M-AUG15 = 5, M-PS16 = {len(ps16)}")
print("Da ghi: posthoc_out/posthoc3b_all_patterns.csv va .json", f"({time.time()-t0:.0f}s)")
