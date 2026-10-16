# HẬU KIỂM đợt 4 (sau khóa protocol v0.4; xem addendum_posthoc_round4_20261014.md). Không sửa file đã khóa.
# Câu hỏi (phản biện nội bộ 2026-10-14, m1): lưới C đã khóa {0.03, 0.1, 0.3, 1} có bị chạm biên không, và mở rộng lưới
# (C = 3, 10, 30, 100) có đổi mô hình được chọn hoặc log loss trong DỮ LIỆU PHÁT TRIỂN không?
# Chỉ dùng cohort P (kết cục chính HbA1c >= 6.5%). KHÔNG đọc cohort L và không dùng bất kỳ dự đoán nào trên L.
# Dùng nguyên hàm tune() của bản khóa (cùng GroupKFold(5) theo PSU, cùng log loss có trọng số), chỉ thay lưới C_GRID.
# Kiểm tái lập trước khi ghi kết quả: log loss ở 4 giá trị C đã khóa phải trùng final_out/tuning_log_P.csv.
# Chạy từ thư mục gốc dự án: python notebooks/10c_posthoc_C_grid_extension.py   (vài phút đến vài chục phút; chỉ LR)
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import final_pipeline as fp

sys.stdout.reconfigure(encoding="utf-8")
RAW, OUT = ROOT / "data" / "raw", ROOT / "posthoc_out"
OUT.mkdir(exist_ok=True)
fp.verify_lock(ROOT, ROOT / "LOCK_protocol_v0.4.json")
print("LOCK OK")
t0 = time.time()

LOCKED = [0.03, 0.1, 0.3, 1.0]
EXT = LOCKED + [3.0, 10.0, 30.0, 100.0]
fp.C_GRID = EXT  # tune() đọc biến toàn cục này khi được gọi; không sửa file src/final_pipeline.py

coh = fp.cohort("P", RAW, threshold=6.5)
print(f"P n={len(coh)} su kien={int(coh['y'].sum())}")
log = []
fp.tune(coh, "LR", log)
df = pd.DataFrame(log)
df["C"] = df["hp"].astype(float)
df = df.drop(columns=["hp"])
print(f"tune xong ({time.time()-t0:.0f}s)")

# ---- kiểm tái lập với log đã khóa (kết cục chính = dòng không có nhãn '5.7')
ref = pd.read_csv(ROOT / "final_out" / "tuning_log_P.csv")
ref = ref[(ref["learner"] == "LR") & ref["label"].isna()].copy()
ref["C"] = ref["hp"].astype(float)
mg = df.merge(ref[["method", "C", "wlogloss"]], on=["method", "C"], suffixes=("", "_locked"))
assert len(mg) == 9 * len(LOCKED), f"so dong khop = {len(mg)} (can {9 * len(LOCKED)})"
gate = float((mg["wlogloss"] - mg["wlogloss_locked"]).abs().max())
print(f"Tai lap log loss o 4 gia tri C da khoa: sai lech toi da = {gate:.2e}")
if gate > 1e-8:
    print("DUNG: khong tai lap duoc log da khoa; khong ghi ket qua.")
    sys.exit(1)

# ---- tóm tắt theo mô hình (BASE, AUG, PS-S0..PS-S6)
rows = []
for m, g in df.groupby("method", sort=False):
    g = g.sort_values("C")
    gl = g[g["C"].isin(LOCKED)]
    c_lock = float(gl.loc[gl["wlogloss"].idxmin(), "C"])
    c_ext = float(g.loc[g["wlogloss"].idxmin(), "C"])
    ll = dict(zip(g["C"], g["wlogloss"]))
    rows.append({
        "method": m, "C_locked_grid": c_lock, "C_extended_grid": c_ext,
        "wlogloss_at_locked_choice": ll[c_lock], "wlogloss_at_extended_choice": ll[c_ext],
        "gain_extended_vs_locked": ll[c_lock] - ll[c_ext],
        "wlogloss_C1": ll[1.0], "wlogloss_C3": ll[3.0],
        "edge_of_locked_grid": c_lock == 1.0, "edge_of_extended_grid": c_ext == EXT[-1],
    })
sm = pd.DataFrame(rows)
df.to_csv(OUT / "posthoc4_C_grid_loss.csv", index=False)
sm.to_csv(OUT / "posthoc4_C_grid_summary.csv", index=False)
pd.set_option("display.width", 200)
print(sm.round(5).to_string(index=False))
res = {
    "gate_max_abs_diff": gate, "grid_locked": LOCKED, "grid_extended": EXT,
    "n_models": int(len(sm)),
    "n_at_locked_edge": int(sm["edge_of_locked_grid"].sum()),
    "n_choice_changes": int((sm["C_locked_grid"] != sm["C_extended_grid"]).sum()),
    "n_at_extended_edge": int(sm["edge_of_extended_grid"].sum()),
    "max_gain_extended_vs_locked": float(sm["gain_extended_vs_locked"].max()),
    "seconds": round(time.time() - t0),
}
(OUT / "posthoc4_C_grid.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
print(json.dumps(res, indent=2))
print("Da ghi posthoc_out/posthoc4_C_grid_loss.csv, posthoc4_C_grid_summary.csv, posthoc4_C_grid.json (chi du lieu phat trien P).")
