"""Pipeline cuối theo protocol v0.4 (+ D-35…D-43).

Giai đoạn A (chỉ P): tuning C, huấn luyện trên toàn bộ P, ngưỡng, hiệu chuẩn lại → lưu mô hình.
Khóa: tạo LOCK_protocol_v0.4.json (mã băm protocol, log, code, mô hình).
Giai đoạn B (L, một lần): kiểm mã băm, dự đoán, chỉ số, CI JK2.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer

import nhanes_audit as na

# ---------------------------------------------------------------- cấu hình định trước
BLOCKS = {
    "B1": ["BMXBMI", "BMXWAIST", "BMXHT", "BMXWT", "WHTR"],
    "B2": ["SBP_MEAN", "DBP_MEAN"],
    "B3": ["BPQ020"],
    "B4": ["SMOKE3", "PAD680", "INDFMPIR", "DMDEDUC2"],
}
CORE = ["RIDAGEYR", "RIAGENDR", "RIDRETH3"]
FEATURES = CORE + [v for vs in BLOCKS.values() for v in vs]
NUM = ["RIDAGEYR", "BMXBMI", "BMXWAIST", "BMXHT", "BMXWT", "WHTR", "SBP_MEAN", "DBP_MEAN",
       "PAD680", "INDFMPIR"]
CAT = ["RIAGENDR", "RIDRETH3", "BPQ020", "SMOKE3", "DMDEDUC2"]
IND = [f"MISS_{b}" for b in BLOCKS]
SCEN = {"S0": [], "S1": ["B1"], "S2": ["B2"], "S3": ["B3"], "S4": ["B4"], "S5": ["B1", "B2"],
        "S6": ["B3", "B4"]}
TRAIN_MASK = ["S1", "S2", "S3", "S4", "S5"]  # mẫu dùng cho augmentation
PRIMARY = ["S1", "S2", "S3", "S4", "S5"]      # estimand chính
C_GRID = [0.03, 0.1, 0.3, 1.0]
AUG_SEEDS = [0, 1, 2, 3, 4]
LGB_GRID = [dict(num_leaves=nl, min_child_samples=mc, learning_rate=lr)
            for nl in (7, 15, 31) for mc in (20, 50) for lr in (0.05, 0.1)]
LGB_BASE = dict(n_estimators=300, verbose=-1, deterministic=True, force_row_wise=True,
                reg_lambda=1.0)
DELTA = 0.005
TARGET_SENS = 0.80
NB_THRESH = [0.01, 0.02, 0.05, 0.10]
S7_PROB = {"low_edu": 0.5, "high_edu": 0.1, "seed": 2026}
FORBIDDEN_PREFIX = ("LBX", "LBD", "DIQ", "RXQ")


# ---------------------------------------------------------------- dữ liệu
def cohort(cycle: str, raw_dir: Path, threshold: float = 6.5, keep_borderline=True) -> pd.DataFrame:
    df, _, _ = na.load_cycle(cycle, raw_dir)
    df = na.derive(na.clean(df))
    wv = na.CYCLES[cycle]["label_weight"]
    coh, _ = na.build_cohort(df, wv, keep_borderline=keep_borderline)
    coh = coh.copy()
    coh["y"] = (coh["LBXGH"] >= threshold).astype(int)
    coh["w"] = coh[wv].astype(float)
    coh["grp"] = coh["SDMVSTRA"].astype(int) * 10 + coh["SDMVPSU"].astype(int)
    return coh


def check_forbidden():
    bad = [c for c in FEATURES if c.startswith(FORBIDDEN_PREFIX)]
    assert not bad, f"K2 fail {bad}"


def X_mask(df: pd.DataFrame, blocks=(), row_mask: np.ndarray | None = None) -> pd.DataFrame:
    """Đủ biến + 4 chỉ báo. blocks bị đặt NaN (toàn bộ dòng, hoặc chỉ các dòng row_mask)."""
    X = df[FEATURES].copy()
    for b in BLOCKS:
        X[f"MISS_{b}"] = 0
    m = np.ones(len(X), bool) if row_mask is None else row_mask
    for b in blocks:
        X.loc[m, BLOCKS[b]] = np.nan
        X.loc[m, f"MISS_{b}"] = 1
    return X


def keep_cols(blocks) -> list[str]:
    drop = {v for b in blocks for v in BLOCKS[b]}
    return [c for c in FEATURES if c not in drop]


def X_drop(df: pd.DataFrame, blocks=()) -> pd.DataFrame:
    cols = keep_cols(blocks)
    X = df[cols].copy()
    dropped = {v for b in blocks for v in BLOCKS[b]}
    assert not dropped & set(X.columns), "K9 fail"
    return X


def augment(X0: pd.DataFrame, y: np.ndarray, rng) -> tuple[pd.DataFrame, np.ndarray]:
    pick = rng.choice(TRAIN_MASK, size=len(X0))
    Xc = X0.copy()
    for s in TRAIN_MASK:
        m = pick == s
        for b in SCEN[s]:
            Xc.loc[m, BLOCKS[b]] = np.nan
            Xc.loc[m, f"MISS_{b}"] = 1
    return pd.concat([X0, Xc], ignore_index=True), np.concatenate([y, y])


# ---------------------------------------------------------------- learners
def lr_model(cols, C):
    num = [c for c in NUM if c in cols]
    cat = [c for c in CAT if c in cols]
    ind = [c for c in cols if c.startswith("MISS_")]
    tr = [("num", make_pipeline(SimpleImputer(strategy="median", add_indicator=True,
                                              keep_empty_features=True),
                                SplineTransformer(n_knots=4, degree=3)), num),
          ("cat", make_pipeline(SimpleImputer(strategy="most_frequent", keep_empty_features=True),
                                OneHotEncoder(handle_unknown="ignore")), cat)]
    if ind:
        tr.append(("ind", "passthrough", ind))
    return make_pipeline(ColumnTransformer(tr), LogisticRegression(C=C, max_iter=5000))


def lgb_model(cfg, seed=0):
    return lgb.LGBMClassifier(random_state=seed, **LGB_BASE, **cfg)


def _prep_lgb(X):
    X = X.copy()
    if "RIDRETH3" in X:
        X["RIDRETH3"] = pd.Categorical(X["RIDRETH3"], categories=[1, 2, 3, 4, 6, 7])
    return X


def fit_model(learner, hp, X, y, sw=None, seed=0):
    if learner == "LR":
        m = lr_model(list(X.columns), hp)
        m.fit(X, y, **({"logisticregression__sample_weight": sw} if sw is not None else {}))
        return m
    m = lgb_model(hp, seed)
    m.fit(_prep_lgb(X), y, sample_weight=sw)
    return m


def predict(learner, m, X):
    return m.predict_proba(_prep_lgb(X) if learner == "LGB" else X)[:, 1]


# ---------------------------------------------------------------- phương pháp
class AugEnsemble:
    """M-AUG: trung bình 5 mô hình, mỗi mô hình một seed augmentation (D-42b)."""

    def __init__(self, learner, hp, weighted=False):
        self.learner, self.hp, self.weighted, self.models = learner, hp, weighted, []

    def fit(self, df):
        X0, y = X_mask(df), df["y"].values
        for s in AUG_SEEDS:
            Xa, ya = augment(X0, y, np.random.default_rng(s))
            sw = np.concatenate([df["w"].values] * 2) / df["w"].mean() if self.weighted else None
            self.models.append(fit_model(self.learner, self.hp, Xa, ya, sw, seed=s))
        return self

    def predict(self, df, blocks=(), row_mask=None):
        X = X_mask(df, blocks, row_mask)
        return np.mean([predict(self.learner, m, X) for m in self.models], axis=0)


class Base:
    def __init__(self, learner, hp, weighted=False):
        self.learner, self.hp, self.weighted = learner, hp, weighted

    def fit(self, df):
        sw = df["w"].values / df["w"].mean() if self.weighted else None
        self.m = fit_model(self.learner, self.hp, X_mask(df), df["y"].values, sw)
        return self

    def predict(self, df, blocks=(), row_mask=None):
        return predict(self.learner, self.m, X_mask(df, blocks, row_mask))


class PatternSub:
    """M-PS: một mô hình con cho mỗi kịch bản trong SCEN; hp riêng cho từng kịch bản."""

    def __init__(self, learner, hps: dict, weighted=False):
        self.learner, self.hps, self.weighted, self.m = learner, hps, weighted, {}

    def fit(self, df):
        sw = df["w"].values / df["w"].mean() if self.weighted else None
        for s, bl in SCEN.items():
            self.m[s] = fit_model(self.learner, self.hps[s], X_drop(df, bl), df["y"].values, sw)
        return self

    def predict_s(self, df, s):
        return predict(self.learner, self.m[s], X_drop(df, SCEN[s]))

    def predict(self, df, blocks=(), row_mask=None):
        s = {tuple(v): k for k, v in SCEN.items()}[tuple(blocks)]
        if row_mask is None:
            return self.predict_s(df, s)
        return np.where(row_mask, self.predict_s(df, s), self.predict_s(df, "S0"))


# ---------------------------------------------------------------- chỉ số
def wlogloss(y, p, w):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.average(y * np.log(p) + (1 - y) * np.log(1 - p), weights=w))


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _wlogit_fit(X, y, w, offset=None, iters=50):
    """Hồi quy logistic có trọng số (Newton), có offset. X gồm cột hằng nếu cần."""
    off = np.zeros(len(y)) if offset is None else offset
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ b + off
        mu = 1 / (1 + np.exp(-eta))
        g = X.T @ (w * (y - mu))
        H = (X * (w * mu * (1 - mu))[:, None]).T @ X
        step = np.linalg.solve(H + 1e-10 * np.eye(len(b)), g)
        b += step
        if np.max(np.abs(step)) < 1e-9:
            break
    return b


def sens_threshold(y, p, w, target=TARGET_SENS):
    """Ngưỡng lớn nhất sao cho độ nhạy có trọng số ≥ target."""
    pos = y == 1
    order = np.argsort(-p[pos])
    ps, ws = p[pos][order], w[pos][order]
    cum = np.cumsum(ws) / ws.sum()
    return float(ps[np.searchsorted(cum, target)])


def metrics(y, p, w, thr=None) -> dict:
    y, p, w = np.asarray(y, float), np.asarray(p, float), np.asarray(w, float)
    pb = np.average(y, weights=w)
    brier = np.average((p - y) ** 2, weights=w)
    lp = _logit(p)
    one = np.ones((len(y), 1))
    citl = _wlogit_fit(one, y, w, offset=lp)[0]
    a_b = _wlogit_fit(np.column_stack([np.ones(len(y)), lp]), y, w)
    # ICI (D-42c): hồi quy logistic spline có trọng số của y theo logit(p)
    sp = SplineTransformer(n_knots=4, degree=3).fit(lp.reshape(-1, 1))
    pc = LogisticRegression(C=1e4, max_iter=5000).fit(sp.transform(lp.reshape(-1, 1)), y,
                                                     sample_weight=w / w.mean())
    pcal = pc.predict_proba(sp.transform(lp.reshape(-1, 1)))[:, 1]
    out = {"skill": 1 - brier / (pb * (1 - pb)), "brier": brier, "prev": pb,
           "auc": roc_auc_score(y, p, sample_weight=w), "citl": citl, "slope": a_b[1],
           "oe": pb / np.average(p, weights=w), "ici": np.average(np.abs(pcal - p), weights=w),
           "logloss": wlogloss(y, p, w)}
    for t in NB_THRESH:
        tp = np.sum(w * ((p >= t) & (y == 1))) / w.sum()
        fp = np.sum(w * ((p >= t) & (y == 0))) / w.sum()
        out[f"nb_{t}"] = tp - fp * t / (1 - t)
    if thr is not None:
        pos = p >= thr
        W = w.sum()
        tp, fp = np.sum(w * pos * (y == 1)), np.sum(w * pos * (y == 0))
        fn, tn = np.sum(w * ~pos * (y == 1)), np.sum(w * ~pos * (y == 0))
        out.update(sens=tp / (tp + fn), spec=tn / (tn + fp), ppv=tp / max(tp + fp, 1e-12),
                   npv=tn / max(tn + fn, 1e-12), referral=(tp + fp) / W)
    return {k: float(v) for k, v in out.items()}


# ---------------------------------------------------------------- JK2 trên L
def jk2_weights(df: pd.DataFrame) -> list[np.ndarray]:
    reps = []
    for h, g in df.groupby("SDMVSTRA"):
        psus = sorted(g["SDMVPSU"].unique())
        assert len(psus) == 2, f"stratum {h} không có đúng 2 PSU"
        w = df["w"].values.copy()
        inh = (df["SDMVSTRA"] == h).values
        w[inh & (df["SDMVPSU"] == psus[0]).values] *= 2
        w[inh & (df["SDMVPSU"] == psus[1]).values] = 0
        reps.append(w)
    return reps


def with_ci(fn, df: pd.DataFrame) -> dict:
    """fn(w) -> dict các ước lượng. Trả về ước lượng, SE, CI JK2 (t, df = số strata)."""
    full = fn(df["w"].values)
    reps = [fn(w) for w in jk2_weights(df)]
    dfree = df["SDMVSTRA"].nunique()
    t = stats.t.ppf(0.975, dfree)
    out = {}
    for k, v in full.items():
        se = float(np.sqrt(sum((r[k] - v) ** 2 for r in reps)))
        out[k] = {"est": v, "se": se, "lo": v - t * se, "hi": v + t * se, "df": dfree}
    return out


def decide(ci: dict, delta=DELTA) -> str:
    """D-44: tương đương thực tế được xét trước; nếu đồng thời CI không chứa 0 thì ghi thêm
    hướng khác biệt thống kê (nhỏ hơn δ)."""
    lo, hi = ci["lo"], ci["hi"]
    direction = "M-AUG tốt hơn" if lo > 0 else ("M-PS tốt hơn" if hi < 0 else None)
    if -delta < lo and hi < delta:
        base = "tương đương thực tế (CI trong ±δ)"
        return base + (f"; khác biệt thống kê nhỏ hơn δ: {direction}" if direction else "")
    return direction or "không kết luận được"


# ---------------------------------------------------------------- tuning trên P (OOF)
def oof(coh: pd.DataFrame, learner: str, method: str, hp, scen_list, s_ps=None):
    """Dự đoán OOF GroupKFold(5) theo PSU. Trả về {scenario: p}."""
    out = {s: np.full(len(coh), np.nan) for s in scen_list}
    for tr, va in GroupKFold(5).split(coh, coh["y"], coh["grp"]):
        T, V = coh.iloc[tr], coh.iloc[va]
        assert not set(T["grp"]) & set(V["grp"]), "K3 fail"
        if method == "PS":
            m = fit_model(learner, hp, X_drop(T, SCEN[s_ps]), T["y"].values)
            out[s_ps][va] = predict(learner, m, X_drop(V, SCEN[s_ps]))
            continue
        mod = (AugEnsemble if method == "AUG" else Base)(learner, hp).fit(T)
        for s in scen_list:
            out[s][va] = mod.predict(V, SCEN[s])
    return out


def tune(coh: pd.DataFrame, learner: str, log: list) -> dict:
    grid = C_GRID if learner == "LR" else LGB_GRID
    y, w = coh["y"].values, coh["w"].values
    chosen, oofs = {}, {}
    # BASE: theo S0
    res = []
    for hp in grid:
        o = oof(coh, learner, "BASE", hp, list(SCEN))
        res.append((wlogloss(y, o["S0"], w), hp, o))
        log.append({"learner": learner, "method": "BASE", "hp": str(hp), "wlogloss": res[-1][0]})
    best = min(res, key=lambda r: r[0])
    chosen["BASE"], oofs["BASE"] = best[1], best[2]
    # AUG: trung bình S0–S5
    res = []
    for hp in grid:
        o = oof(coh, learner, "AUG", hp, list(SCEN))
        ll = np.mean([wlogloss(y, o[s], w) for s in ["S0"] + TRAIN_MASK])
        res.append((ll, hp, o))
        log.append({"learner": learner, "method": "AUG", "hp": str(hp), "wlogloss": ll})
    best = min(res, key=lambda r: r[0])
    chosen["AUG"], oofs["AUG"] = best[1], best[2]
    # PS: từng mô hình con
    chosen["PS"], oofs["PS"] = {}, {}
    for s in SCEN:
        res = []
        for hp in grid:
            o = oof(coh, learner, "PS", hp, [s], s_ps=s)
            res.append((wlogloss(y, o[s], w), hp, o[s]))
            log.append({"learner": learner, "method": f"PS-{s}", "hp": str(hp), "wlogloss": res[-1][0]})
        best = min(res, key=lambda r: r[0])
        chosen["PS"][s], oofs["PS"][s] = best[1], best[2]
    return {"chosen": chosen, "oof": oofs}


def recalibrator(y, p, w):
    """Hiệu chuẩn lại logistic (a + b·logit p), fit trên OOF S0 của P, có trọng số (D-43)."""
    return _wlogit_fit(np.column_stack([np.ones(len(y)), _logit(p)]), y, w / w.mean())


def apply_recal(ab, p):
    return 1 / (1 + np.exp(-(ab[0] + ab[1] * _logit(p))))


# ---------------------------------------------------------------- điểm Bang (D-38)
def bang_score(df: pd.DataFrame) -> np.ndarray:
    age = df["RIDAGEYR"]
    s = np.select([age < 40, age < 50, age < 60], [0, 1, 2], 3).astype(float)
    s += (df["RIAGENDR"] == 1).astype(float)
    # tiền sử gia đình = 0; thể lực = 0 (D-38)
    htn = (df["BPQ020"] == 1) | (df["SBP_MEAN"] >= 140) | (df["DBP_MEAN"] >= 90)
    s += htn.astype(float)
    bmi, wc_in, male = df["BMXBMI"], df["BMXWAIST"] / 2.54, df["RIAGENDR"] == 1
    ext = (bmi >= 40) | (male & (wc_in >= 50)) | (~male & (wc_in >= 49))
    ob = ((bmi >= 30) & (bmi < 40)) | (male & (wc_in >= 40) & (wc_in < 50)) | (~male & (wc_in >= 35) & (wc_in < 49))
    ov = ((bmi >= 25) & (bmi < 30)) | (male & (wc_in >= 37) & (wc_in < 40)) | (~male & (wc_in >= 31.5) & (wc_in < 35))
    s += np.select([ext, ob, ov], [3, 2, 1], 0)
    return s.values


# ---------------------------------------------------------------- khóa
def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lock_manifest(root: Path, files: list[Path]) -> dict:
    return {str(f.relative_to(root)).replace("\\", "/"): sha(f) for f in files}


def verify_lock(root: Path, lock_path: Path):
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    bad = [f for f, h in lock["files"].items() if sha(root / f) != h]
    if bad:
        raise PermissionError(f"LOCK không khớp (file đã đổi sau khi khóa): {bad}")
    return lock


def save_pickle(obj, path: Path):
    path.write_bytes(pickle.dumps(obj))


def load_pickle(path: Path):
    return pickle.loads(path.read_bytes())
