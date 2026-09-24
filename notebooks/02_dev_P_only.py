# %% [markdown]
# # 02 — Pipeline phát triển, CHỈ dữ liệu P (protocol v0.3)
# - Tham số cố định (D-21), 1 seed, không tuning. **Không nạp L** (K10).
# - Mục đích: kiểm tra pipeline và các chốt rò rỉ K2, K3, K6, K7, K9, K10; ước lượng sơ bộ độ lớn Δ trên OOF của P để hỗ trợ chọn δ.
# - Kết quả này **không phải** kết quả nghiên cứu và không được đưa vào bài như bằng chứng.

# %%
import sys
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
import dev_pipeline as dp

OUT = ROOT / "dev_out"
OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 160)
dp.check_features()  # K2

# %%
try:  # K10
    dp.load_L_guarded(ROOT / "data" / "raw", ROOT)
    raise SystemExit("K10 FAIL: L được nạp khi chưa khóa")
except PermissionError as e:
    print("K10 OK:", e)

# %%
coh = dp.load_P(ROOT / "data" / "raw")
print("n =", len(coh), "| sự kiện =", int(coh.y.sum()), "| nhóm PSU =", coh.grp.nunique())

# %% [markdown]
# ## K7 — AUROC từng biến đơn lẻ (phải < 0,85)

# %%
sf = dp.single_feature_auc(coh)
sf.to_csv(OUT / "K7_single_feature_auc.csv", index=False)
print(sf.head(8))
assert sf.auc.max() < 0.85, "K7 fail"

# %% [markdown]
# ## K6 — Hoán vị nhãn (AUROC OOF phải trong 0,45–0,55)

# %%
perm_auc = dp.permutation_check(coh)
print("AUROC nhãn hoán vị:", round(perm_auc, 3))

# %% [markdown]
# ## OOF trên P: M-BASE, M-AUG, M-PS × S0–S5 (K3, K9 được assert bên trong)

# %%
oof = dp.run_cv(coh, seed=0)
oof.to_csv(OUT / "oof_P_seed0.csv", index=False)
summ = dp.summarize(oof, coh)
summ.to_csv(OUT / "summary_P_seed0.csv", index=False)
print(summ.pivot(index="scenario", columns="method", values="brier_w").round(5))
print(summ.pivot(index="scenario", columns="method", values="auc_w").round(3))
delta = dp.primary_delta(summ)
print(delta)

# %%
checks = {"K2": "OK", "K3": "OK (assert trong run_cv)", "K9": "OK (assert trong X_of)",
          "K10": "OK", "K6_perm_auc": perm_auc, "K6_pass": 0.45 <= perm_auc <= 0.55,
          "K7_max_single_auc": float(sf.auc.max()), "K7_pass": bool(sf.auc.max() < 0.85),
          "dev_delta_P_OOF": delta, "note": "Chỉ P, 1 seed, tham số cố định; không phải kết quả nghiên cứu"}
dp.to_json(checks, OUT / "dev_checks.json")
print(checks)
