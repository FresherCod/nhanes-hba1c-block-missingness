"""Pipeline phát triển theo protocol v0.3 — CHỈ dùng P (2017–03/2020).

- Tham số LightGBM cố định trước cổng (D-21); không tuning.
- L bị khóa: `load_L_guarded` từ chối nạp nếu chưa có LOCK file (K10).
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

import nhanes_audit as na

BLOCKS = {
    "B1": ["BMXBMI", "BMXWAIST", "BMXHT", "BMXWT", "WHTR"],
    "B2": ["SBP_MEAN", "DBP_MEAN"],
    "B3": ["BPQ020"],
    "B4": ["SMOKE3", "PAD680", "INDFMPIR", "DMDEDUC2"],
}
CORE = ["RIDAGEYR", "RIAGENDR", "RIDRETH3"]
IND = [f"MISS_{b}" for b in BLOCKS]  # chỉ báo "khối bị che"
FEATURES = CORE + [v for vs in BLOCKS.values() for v in vs]
SCEN = {"S0": [], "S1": ["B1"], "S2": ["B2"], "S3": ["B3"], "S4": ["B4"], "S5": ["B1", "B2"]}
MASK_SCEN = ["S1", "S2", "S3", "S4", "S5"]

# Tham số cố định trước cổng (D-21) — KHÔNG chỉnh theo kết quả
LGB_FIXED = dict(n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=50,
                 subsample=1.0, colsample_bytree=1.0, reg_lambda=1.0, verbose=-1,
                 deterministic=True, force_row_wise=True)
THRESHOLD = 6.5


# ---------------------------------------------------------------- dữ liệu
def load_P(raw_dir: Path) -> pd.DataFrame:
    df, _, _ = na.load_cycle("P", raw_dir)
    df = na.derive(na.clean(df))
    coh, _ = na.build_cohort(df, na.CYCLES["P"]["label_weight"], keep_borderline=True)
    coh = coh.copy()
    coh["y"] = (coh["LBXGH"] >= THRESHOLD).astype(int)
    coh["w"] = coh[na.CYCLES["P"]["label_weight"]]
    coh["grp"] = coh["SDMVSTRA"].astype(int) * 10 + coh["SDMVPSU"].astype(int)
    return coh


def load_L_guarded(raw_dir: Path, root: Path):
    """K10: không nạp L khi chưa khóa protocol."""
    locks = sorted(root.glob("LOCK_protocol_v*.json"))
    if not locks:
        raise PermissionError("L đang bị khóa: chưa có LOCK_protocol_v*.json (protocol chưa khóa)")
    raise NotImplementedError("Đánh giá trên L sẽ viết sau khi khóa protocol")


def check_features():
    bad = na.check_forbidden(FEATURES)
    assert not bad, f"K2 fail: {bad}"


def X_of(df: pd.DataFrame, masked_blocks=(), drop_blocks=()) -> pd.DataFrame:
    """masked_blocks: đặt NaN + chỉ báo = 1 (M-BASE/M-AUG).
    drop_blocks: bỏ hẳn cột (M-PS) và không có cột chỉ báo."""
    X = df[FEATURES].copy()
    X["RIDRETH3"] = X["RIDRETH3"].astype("category")
    if drop_blocks:
        cols = [c for b in drop_blocks for c in BLOCKS[b]]
        X = X.drop(columns=cols)
        # K9: mô hình con không được thấy cột của khối bị bỏ
        assert not set(cols) & set(X.columns)
        return X
    for b in BLOCKS:
        X[f"MISS_{b}"] = 0
    for b in masked_blocks:
        X[BLOCKS[b]] = np.nan
        X[f"MISS_{b}"] = 1
    return X


def augment(train: pd.DataFrame, rng: np.random.Generator) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Mỗi dòng train + 1 bản sao bị che theo một kịch bản ngẫu nhiên trong S1–S5.
    Gọi SAU khi chia fold (K3). Trả về X, y, nhóm (bản sao giữ nhóm gốc)."""
    X0 = X_of(train)
    pick = rng.choice(MASK_SCEN, size=len(train))
    Xc = X0.copy()
    for s in MASK_SCEN:
        m = pick == s
        for b in SCEN[s]:
            Xc.loc[m, BLOCKS[b]] = np.nan
            Xc.loc[m, f"MISS_{b}"] = 1
    X = pd.concat([X0, Xc], ignore_index=True)
    X["RIDRETH3"] = X["RIDRETH3"].astype(X0["RIDRETH3"].dtype)
    y = np.concatenate([train["y"].values] * 2)
    g = np.concatenate([train["grp"].values] * 2)
    return X, y, g


def fit(X, y, seed):
    m = lgb.LGBMClassifier(random_state=seed, **LGB_FIXED)
    m.fit(X, y)
    return m


# ---------------------------------------------------------------- chỉ số
def wbrier(y, p, w):
    return float(np.average((p - y) ** 2, weights=w))


def wauc(y, p, w):
    return float(roc_auc_score(y, p, sample_weight=w))


# ---------------------------------------------------------------- CV trên P
def run_cv(coh: pd.DataFrame, seed: int = 0, n_splits: int = 5, y_col: str = "y") -> pd.DataFrame:
    """Trả về dự đoán OOF dạng dài: (idx, method, scenario, p)."""
    rng = np.random.default_rng(seed)
    gkf = GroupKFold(n_splits=n_splits)
    out = []
    for k, (tr, va) in enumerate(gkf.split(coh, coh[y_col], coh["grp"])):
        trd, vad = coh.iloc[tr], coh.iloc[va]
        # K3: không nhóm nào ở cả train và validation
        assert not set(trd["grp"]) & set(vad["grp"]), "K3 fail: nhóm PSU rò giữa train/val"
        ytr = trd[y_col].values
        base = fit(X_of(trd), ytr, seed)
        Xa, ya, ga = augment(trd.assign(y=ytr), rng)
        assert set(ga) <= set(trd["grp"]), "K3 fail: bản sao augmentation mang nhóm ngoài train"
        aug = fit(Xa, ya, seed)
        for s, blocks in SCEN.items():
            Xv = X_of(vad, masked_blocks=blocks)
            ps = fit(X_of(trd, drop_blocks=blocks), ytr, seed)
            preds = {"M-BASE": base.predict_proba(Xv)[:, 1],
                     "M-AUG": aug.predict_proba(Xv)[:, 1],
                     "M-PS": ps.predict_proba(X_of(vad, drop_blocks=blocks))[:, 1]}
            for meth, p in preds.items():
                out.append(pd.DataFrame({"idx": vad.index, "fold": k, "method": meth,
                                         "scenario": s, "p": p}))
    return pd.concat(out, ignore_index=True)


def summarize(oof: pd.DataFrame, coh: pd.DataFrame, y_col: str = "y") -> pd.DataFrame:
    d = oof.merge(coh[[y_col, "w"]], left_on="idx", right_index=True)
    rows = []
    for (m, s), g in d.groupby(["method", "scenario"]):
        rows.append({"method": m, "scenario": s,
                     "brier_w": wbrier(g[y_col], g["p"], g["w"]),
                     "brier_unw": float(np.mean((g["p"] - g[y_col]) ** 2)),
                     "auc_w": wauc(g[y_col], g["p"], g["w"]),
                     "mean_p_w": float(np.average(g["p"], weights=g["w"])),
                     "prev_w": float(np.average(g[y_col], weights=g["w"]))})
    return pd.DataFrame(rows)


def primary_delta(summary: pd.DataFrame) -> dict:
    t = summary.pivot(index="scenario", columns="method", values="brier_w")
    ms = t.loc[MASK_SCEN]
    return {"delta_AUG_minus_PS_meanS1S5": float((ms["M-AUG"] - ms["M-PS"]).mean()),
            "delta_AUG_minus_BASE_meanS1S5": float((ms["M-AUG"] - ms["M-BASE"]).mean()),
            "delta_AUG_minus_PS_S0": float(t.loc["S0", "M-AUG"] - t.loc["S0", "M-PS"])}


# ---------------------------------------------------------------- kiểm tra rò rỉ
def single_feature_auc(coh: pd.DataFrame) -> pd.DataFrame:
    """K7: AUROC của từng biến đơn lẻ (lấy max(auc, 1-auc)), bỏ qua giá trị thiếu."""
    rows = []
    for v in FEATURES:
        ok = coh[v].notna()
        x = coh.loc[ok, v].astype(float)
        if x.nunique() < 2:
            continue
        a = roc_auc_score(coh.loc[ok, "y"], x)
        rows.append({"var": v, "auc": max(a, 1 - a), "n": int(ok.sum())})
    return pd.DataFrame(rows).sort_values("auc", ascending=False)


def permutation_check(coh: pd.DataFrame, seed: int = 123) -> float:
    """K6: nhãn hoán vị → AUROC OOF của M-BASE ở S0 phải ≈ 0,5."""
    rng = np.random.default_rng(seed)
    c = coh.copy()
    c["y_perm"] = rng.permutation(c["y"].values)
    gkf = GroupKFold(n_splits=5)
    p = pd.Series(np.nan, index=c.index)
    for tr, va in gkf.split(c, c["y_perm"], c["grp"]):
        m = fit(X_of(c.iloc[tr]), c["y_perm"].values[tr], seed)
        p.iloc[va] = m.predict_proba(X_of(c.iloc[va]))[:, 1]
    return float(roc_auc_score(c["y_perm"], p))


def to_json(obj, path: Path):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
