"""Audit dữ liệu NHANES cho protocol v0.2 (không huấn luyện mô hình).

Cùng một hàm dựng cohort cho P và L (kiểm tra rò rỉ K8).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.{ext}"

CYCLES = {
    "P": {"year": 2017, "files": {k: f"P_{k}" for k in
          ["DEMO", "GHB", "DIQ", "BMX", "BPXO", "BPQ", "MCQ", "SMQ", "PAQ", "RHQ"]},
          "label_weight": "WTMECPRP"},
    "L": {"year": 2021, "files": {k: f"{k}_L" for k in
          ["DEMO", "GHB", "DIQ", "BMX", "BPXO", "BPQ", "MCQ", "SMQ", "PAQ", "RHQ"]},
          "label_weight": "WTPH2YR"},
}

# Biến theo khối (protocol mục 4). Biến chỉ có ở một chu kỳ vẫn được liệt kê; audit báo có/không.
BLOCKS = {
    "core": ["RIDAGEYR", "RIAGENDR", "RIDRETH3"],
    "B1": ["BMXWT", "BMXHT", "BMXBMI", "BMXWAIST"],
    "B2": ["BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3"],
    "B3": ["BPQ020", "MCQ300C", "RHQ162"],
    "B4": ["SMQ020", "SMQ040", "PAD680", "PAQ650", "PAQ665", "PAD790Q", "PAD810Q",
           "INDFMPIR", "DMDEDUC2"],
}
COHORT_VARS = ["SEQN", "RIDSTATR", "RIDEXPRG", "DIQ010", "DIQ050", "DIQ070", "LBXGH",
               "SDMVSTRA", "SDMVPSU", "WTMECPRP", "WTMEC2YR", "WTPH2YR", "WTINTPRP", "WTINT2YR"]

# Mã từ chối / không biết cần chuyển thành NaN. Được kiểm lại bằng bảng special_codes.
SPECIAL = {
    **{v: [7, 9] for v in ["BPQ020", "MCQ300C", "RHQ162", "SMQ020", "SMQ040",
                           "PAQ650", "PAQ665", "DMDEDUC2", "DIQ050", "DIQ070"]},
    **{v: [7777, 9999] for v in ["PAD680", "PAD790Q", "PAD810Q"]},
}

# Kiểm tra rò rỉ K2: không biến dự báo nào được có các tiền tố / tên này.
FORBIDDEN_PREFIX = ("LBX", "LBD", "DIQ", "RXQ")
FORBIDDEN_NAMES = {"BPQ080", "BPQ090D", "BPQ100D", "WTMECPRP", "WTPH2YR", "SDMVPSU", "SDMVSTRA"}


def predictor_list() -> list[str]:
    return [v for b in BLOCKS.values() for v in b]


def check_forbidden(cols) -> list[str]:
    return [c for c in cols if c.startswith(FORBIDDEN_PREFIX) or c in FORBIDDEN_NAMES]


# ---------------------------------------------------------------- tải và đọc
def download(cycle: str, key: str, raw_dir: Path) -> dict:
    """Tải một tệp .xpt vào raw_dir (có cache). Trả về dòng manifest."""
    c = CYCLES[cycle]
    name = c["files"][key]
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / f"{name}.xpt"
    rec = {"cycle": cycle, "key": key, "name": name, "path": str(dest), "status": "cached"}
    if not dest.exists():
        rec["status"] = "missing"
        for ext in ("xpt", "XPT"):
            url = BASE.format(year=c["year"], name=name, ext=ext)
            r = requests.get(url, timeout=120)
            # CDC trả HTML (200) cho tệp không tồn tại ở một số đường dẫn -> kiểm chữ ký XPORT.
            if r.status_code == 200 and r.content[:6] == b"HEADER":
                dest.write_bytes(r.content)
                rec.update(status="downloaded", url=url)
                break
    if dest.exists():
        b = dest.read_bytes()
        rec.update(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    return rec


def read_xpt(path: str | Path) -> pd.DataFrame:
    df = pd.read_sas(path, format="xport")
    df.columns = [c.upper() for c in df.columns]
    # pandas đọc số 0 của SAS XPORT thành ~5.4e-79 -> đưa về 0 thật
    num = df.select_dtypes("number").columns
    df[num] = df[num].mask(df[num].abs() < 1e-70, 0.0)
    # cột ký tự đọc thành bytes -> chuỗi; b'' -> NaN
    for c in df.select_dtypes("object").columns:
        df[c] = df[c].map(lambda x: x.decode("latin-1") if isinstance(x, bytes) else x).replace("", np.nan)
    return df


def load_cycle(cycle: str, raw_dir: Path) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    """Ghép mọi tệp của một chu kỳ theo SEQN, trái từ DEMO. Trả về (df, manifest, key_checks)."""
    manifest, checks, frames = [], [], {}
    for key in CYCLES[cycle]["files"]:
        rec = download(cycle, key, raw_dir)
        manifest.append(rec)
        if rec["status"] == "missing":
            continue
        d = read_xpt(rec["path"])
        checks.append({"cycle": cycle, "file": rec["name"], "rows": len(d),
                       "seqn_unique": bool(d["SEQN"].is_unique), "n_cols": d.shape[1]})
        frames[key] = d
    if "DEMO" not in frames:
        raise RuntimeError(f"{cycle}: thiếu DEMO, không thể tiếp tục")
    df = frames.pop("DEMO")
    for key, d in frames.items():
        dup = [c for c in d.columns if c in df.columns and c != "SEQN"]
        if dup:  # ví dụ trọng số lặp lại ở nhiều tệp: giữ bản ở tệp gốc, đổi tên bản lặp
            d = d.rename(columns={c: f"{c}__{key}" for c in dup})
        n0 = len(df)
        df = df.merge(d, on="SEQN", how="left", validate="one_to_one")
        assert len(df) == n0, f"{cycle}/{key}: ghép làm đổi số dòng"
    df["CYCLE"] = cycle
    return df, manifest, checks


# ---------------------------------------------------------------- làm sạch và dẫn xuất
def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for v, codes in SPECIAL.items():
        if v in df:
            df[v] = df[v].where(~df[v].isin(codes))
    return df


def special_code_counts(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v, codes in SPECIAL.items():
        if v in df:
            for c in codes:
                rows.append({"cycle": df["CYCLE"].iat[0], "var": v, "code": c,
                             "n": int((df[v] == c).sum())})
    return pd.DataFrame(rows)


def derive(df: pd.DataFrame) -> pd.DataFrame:
    """Biến dẫn xuất chỉ dùng giá trị của chính từng người (không thống kê quần thể)."""
    df = df.copy()
    if {"BMXWAIST", "BMXHT"} <= set(df):
        df["WHTR"] = df["BMXWAIST"] / df["BMXHT"]
    sy = [c for c in ["BPXOSY1", "BPXOSY2", "BPXOSY3"] if c in df]
    di = [c for c in ["BPXODI1", "BPXODI2", "BPXODI3"] if c in df]
    df["SBP_MEAN"] = df[sy].mean(axis=1) if sy else np.nan
    df["DBP_MEAN"] = df[di].mean(axis=1) if di else np.nan
    # Hút thuốc: 0 = chưa từng, 1 = đã bỏ, 2 = hiện tại
    if {"SMQ020", "SMQ040"} <= set(df):
        s = pd.Series(np.nan, index=df.index)
        s[df["SMQ020"] == 2] = 0
        s[(df["SMQ020"] == 1) & (df["SMQ040"] == 3)] = 1
        s[(df["SMQ020"] == 1) & df["SMQ040"].isin([1, 2])] = 2
        df["SMOKE3"] = s
    # Thể lực giải trí có/không — CHƯA CHỐT (D-19): quy tắc tạm, cần xem value_counts trong audit
    if {"PAQ650", "PAQ665"} <= set(df):
        a = (df["PAQ650"] == 1) | (df["PAQ665"] == 1)
        known = df["PAQ650"].notna() | df["PAQ665"].notna()
        df["LTPA_ANY"] = a.astype(float).where(known)
    elif {"PAD790Q", "PAD810Q"} <= set(df):
        a = (df["PAD790Q"] > 0) | (df["PAD810Q"] > 0)
        known = df["PAD790Q"].notna() | df["PAD810Q"].notna()
        df["LTPA_ANY"] = a.astype(float).where(known)
    # ĐTĐ thai kỳ: nam = 0
    if "RHQ162" in df:
        g = df["RHQ162"].map({1: 1.0, 2: 0.0})
        df["GDM"] = g.where(df["RIAGENDR"] != 1, 0.0)
    return df


# ---------------------------------------------------------------- cohort (K8: một hàm cho P và L)
def build_cohort(df: pd.DataFrame, weight_var: str, keep_borderline: bool = True):
    """Trả về (cohort_df, flow). Mỗi bước ghi n và tổng trọng số của những người còn lại."""
    flow = []
    m = pd.Series(True, index=df.index)

    def step(name, cond):
        nonlocal m
        m = m & cond.fillna(False)
        w = df.loc[m, weight_var] if weight_var in df else pd.Series(dtype=float)
        flow.append({"step": name, "n": int(m.sum()), "sum_w": float(w.sum())})

    step("C1 in DEMO", pd.Series(True, index=df.index))
    step("C2 age>=20", df["RIDAGEYR"] >= 20)
    step("C3 MEC examined", df["RIDSTATR"] == 2)
    step("C4 has LBXGH", df["LBXGH"].notna())
    step("C5 label weight>0", df.get(weight_var, pd.Series(np.nan, index=df.index)) > 0)
    preg = df["RIDEXPRG"] == 1 if "RIDEXPRG" in df else pd.Series(False, index=df.index)
    step("C6 not pregnant", ~preg)
    excl = [1, 7, 9] if keep_borderline else [1, 3, 7, 9]
    # DIQ010 thiếu hẳn -> không xác định được tình trạng chẩn đoán -> loại
    step("C7 not diagnosed (DIQ010)", df["DIQ010"].notna() & ~df["DIQ010"].isin(excl))
    if "DIQ070" in df:
        step("C8 no diabetes pills", ~(df["DIQ070"] == 1))
    return df.loc[m].copy(), pd.DataFrame(flow)


# ---------------------------------------------------------------- tóm tắt
def wmean(x, w):
    ok = x.notna() & w.notna()
    return float(np.average(x[ok], weights=w[ok])) if ok.any() else np.nan


def events_table(coh: pd.DataFrame, weight_var: str, thresholds=(6.5, 5.7, 6.35, 6.65)):
    rows = []
    for t in thresholds:
        y = (coh["LBXGH"] >= t).astype(float)
        rows.append({"cycle": coh["CYCLE"].iat[0], "threshold": t, "n": len(coh),
                     "events": int(y.sum()), "prev_unweighted": float(y.mean()),
                     "prev_weighted": wmean(y, coh[weight_var])})
    return pd.DataFrame(rows)


def subgroup_events(coh: pd.DataFrame, weight_var: str, t: float = 6.5):
    c = coh.copy()
    c["y"] = (c["LBXGH"] >= t).astype(float)
    c["AGEGRP"] = pd.cut(c["RIDAGEYR"], [19, 44, 64, 200], labels=["20-44", "45-64", "65+"])
    c["PIRGRP"] = pd.cut(c["INDFMPIR"], [-1, 1.3, 3.5, 10], labels=["<1.3", "1.3-3.5", ">3.5"])
    rows = []
    for g in ["AGEGRP", "RIAGENDR", "RIDRETH3", "PIRGRP"]:
        for lvl, d in c.groupby(g, observed=True, dropna=False):
            rows.append({"cycle": c["CYCLE"].iat[0], "group": g, "level": str(lvl), "n": len(d),
                         "events": int(d["y"].sum()), "prev_weighted": wmean(d["y"], d[weight_var])})
    return pd.DataFrame(rows)


def weight_design_summary(df: pd.DataFrame, coh: pd.DataFrame, weight_var: str):
    w = coh[weight_var]
    strata = df.groupby("SDMVSTRA")["SDMVPSU"].nunique()
    return {
        "cycle": df["CYCLE"].iat[0], "weight_var": weight_var,
        "weight_in_file": weight_var in df,
        "n_zero_weight_full": int((df.get(weight_var, pd.Series(dtype=float)) == 0).sum()),
        "sum_w_full": float(df.get(weight_var, pd.Series(dtype=float)).sum()),
        "sum_w_cohort": float(w.sum()),
        "cv_w_cohort": float(w.std() / w.mean()),
        "max_over_median_w": float(w.max() / w.median()),
        "n_strata": int(strata.size), "psu_per_stratum": sorted(strata.unique().tolist()),
        "n_strata_in_cohort": int(coh["SDMVSTRA"].nunique()),
    }


def missingness(coh: pd.DataFrame):
    rows = []
    for b, vs in BLOCKS.items():
        for v in vs:
            present = v in coh
            rows.append({"cycle": coh["CYCLE"].iat[0], "block": b, "var": v, "present": present,
                         "pct_missing": float(coh[v].isna().mean() * 100) if present else np.nan})
    return pd.DataFrame(rows)


def block_patterns(coh: pd.DataFrame, block_vars: dict):
    """Mẫu thiếu tự nhiên ở mức khối: một khối được coi là 'thiếu' khi mọi biến của nó đều thiếu."""
    pat = pd.DataFrame({b: coh[[v for v in vs if v in coh]].isna().all(axis=1)
                        for b, vs in block_vars.items() if any(v in coh for v in vs)})
    key = pat.apply(lambda r: "+".join([b for b in pat.columns if r[b]]) or "none", axis=1)
    out = key.value_counts().rename_axis("missing_blocks").reset_index(name="n")
    out.insert(0, "cycle", coh["CYCLE"].iat[0])
    return out


def drift(cohP, cohL, wP, wL, vars_):
    rows = []
    for v in vars_:
        if v in cohP and v in cohL:
            rows.append({"var": v, "mean_w_P": wmean(cohP[v], cohP[wP]),
                         "mean_w_L": wmean(cohL[v], cohL[wL])})
    return pd.DataFrame(rows)


def gates(evL: pd.DataFrame, miss: pd.DataFrame, checks: list[dict], wds: list[dict],
          seqn_overlap: int, min_events: int = 100) -> dict:
    ev65 = int(evL.loc[evL.threshold == 6.5, "events"].iat[0])
    ev57 = int(evL.loc[evL.threshold == 5.7, "events"].iat[0])
    need_both = miss[miss.block.isin(["core", "B1"])]
    pres = need_both.pivot_table(index="var", columns="cycle", values="present", aggfunc="first")
    b2 = miss[miss.block == "B2"].pivot_table(index="var", columns="cycle", values="present",
                                               aggfunc="first")
    blk_ok = {}
    for b in ["B3", "B4"]:
        p = miss[miss.block == b].pivot_table(index="var", columns="cycle", values="present",
                                              aggfunc="first")
        blk_ok[b] = int(p.all(axis=1).sum())
    return {
        "G1_integrity": {
            "all_seqn_unique": all(c["seqn_unique"] for c in checks),
            "label_weight_present": all(w["weight_in_file"] for w in wds),
            "seqn_overlap_P_L": seqn_overlap,
            "pass": all(c["seqn_unique"] for c in checks)
                    and all(w["weight_in_file"] for w in wds) and seqn_overlap == 0,
        },
        "G2_events_L": {"events_6.5": ev65, "events_5.7": ev57, "min": min_events,
                        "pass": ev65 >= min_events,
                        "action_if_fail": "D-03: chuyển nhãn chính sang 5,7%" if ev65 < min_events else None},
        "G3_harmonization": {
            "core_B1_all_present_both": bool(pres.all(axis=None)),
            "B2_vars_present_both": int(b2.all(axis=1).sum()),
            "B3_vars_present_both": blk_ok["B3"], "B4_vars_present_both": blk_ok["B4"],
            "pass": bool(pres.all(axis=None)) and int(b2.all(axis=1).sum()) >= 2
                    and blk_ok["B3"] >= 1 and blk_ok["B4"] >= 1,
            "note": "Có mặt ≠ cùng định nghĩa: vẫn phải đọc codebook cho thể lực (D-19)",
        },
    }


def to_json(obj, path: Path):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
