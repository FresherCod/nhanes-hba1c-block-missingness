# %% [markdown]
# # 01 — Audit dữ liệu (protocol v0.2)
# Chỉ audit: **không huấn luyện mô hình, không tính chỉ số dự báo**.
# Kết quả ghi vào `audit_out/`. Cổng G1–G3 được đánh giá tự động; G4, G5 cần người.
# Chạy lần đầu sẽ tải khoảng 20 tệp .xpt công khai từ wwwn.cdc.gov vào `data/raw/`.

# %%
import sys
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
import nhanes_audit as na

RAW = ROOT / "data" / "raw"
OUT = ROOT / "audit_out"
OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 160)

# %% [markdown]
# ## 1. Tải, ghép, kiểm tra khóa (G1, K1)

# %%
raw, manifest, checks = {}, [], []
for cyc in ["P", "L"]:
    df, man, chk = na.load_cycle(cyc, RAW)
    raw[cyc], manifest, checks = df, manifest + man, checks + chk
pd.DataFrame(manifest).to_csv(OUT / "manifest.csv", index=False)
pd.DataFrame(checks).to_csv(OUT / "key_checks.csv", index=False)
seqn_overlap = len(set(raw["P"].SEQN) & set(raw["L"].SEQN))
print(pd.DataFrame(manifest)[["cycle", "name", "status", "bytes"]])
print(pd.DataFrame(checks))
print("SEQN chung giữa P và L:", seqn_overlap)

# %% [markdown]
# ## 2. Mã đặc biệt (7/9, 7777/9999) trước khi làm sạch

# %%
spec = pd.concat([na.special_code_counts(raw[c]) for c in raw])
spec.to_csv(OUT / "special_codes.csv", index=False)
print(spec[spec.n > 0])

# %% [markdown]
# ## 3. Bảng chéo cho định nghĩa "chưa chẩn đoán" (D-04, C8)
# Kiểm tra DIQ050/DIQ070 có được hỏi người không chẩn đoán hay không.

# %%
for c in raw:
    d = raw[c][raw[c].RIDAGEYR >= 20]
    cols = [x for x in ["DIQ050", "DIQ070"] if x in d]
    for x in cols:
        print(c, x)
        print(pd.crosstab(d["DIQ010"].fillna(-1), d[x].fillna(-1)), "\n")

# %% [markdown]
# ## 4. Làm sạch, dẫn xuất, dựng cohort bằng CÙNG một hàm (K8)

# %%
clean = {c: na.derive(na.clean(raw[c])) for c in raw}
W = {c: na.CYCLES[c]["label_weight"] for c in raw}
coh, flows = {}, []
for c in clean:
    coh[c], f = na.build_cohort(clean[c], W[c], keep_borderline=True)
    f.insert(0, "cycle", c)
    flows.append(f)
flow = pd.concat(flows)
flow.to_csv(OUT / "cohort_flow.csv", index=False)
print(flow)

# Độ nhạy D-04: loại cả borderline
for c in clean:
    alt, _ = na.build_cohort(clean[c], W[c], keep_borderline=False)
    print(c, "n nếu loại DIQ010=3:", len(alt), "| chính:", len(coh[c]))

# %% [markdown]
# ## 5. Số sự kiện (G2) — nhãn chính, dự phòng và độ nhạy thiết bị (D-06)

# %%
ev = pd.concat([na.events_table(coh[c], W[c]) for c in coh])
ev.to_csv(OUT / "events.csv", index=False)
print(ev)
sub = pd.concat([na.subgroup_events(coh[c], W[c]) for c in coh])
sub.to_csv(OUT / "subgroup_events.csv", index=False)
print(sub[sub.cycle == "L"])

# Phân phối HbA1c gần ngưỡng (D-06)
for c in coh:
    near = coh[c].LBXGH.between(6.2, 6.8)
    print(c, "số người có LBXGH trong [6.2, 6.8]:", int(near.sum()))
    print(coh[c].loc[near, "LBXGH"].round(1).value_counts().sort_index().to_dict())

# %% [markdown]
# ## 6. Trọng số và thiết kế (D-05, D-13)

# %%
wds = [na.weight_design_summary(clean[c], coh[c], W[c]) for c in coh]
pd.DataFrame(wds).to_csv(OUT / "weights_design.csv", index=False)
print(pd.DataFrame(wds).T)

# %% [markdown]
# ## 7. Có mặt biến, thiếu tự nhiên, mẫu thiếu theo khối (G3)

# %%
miss = pd.concat([na.missingness(coh[c]) for c in coh])
miss.to_csv(OUT / "missingness.csv", index=False)
print(miss.pivot_table(index=["block", "var"], columns="cycle",
                       values=["present", "pct_missing"], aggfunc="first"))

derived_blocks = {"B1": ["BMXBMI", "WHTR"], "B2": ["SBP_MEAN", "DBP_MEAN"],
                  "B3": ["BPQ020", "MCQ300C", "GDM"],
                  "B4": ["SMOKE3", "PAD680", "LTPA_ANY", "INDFMPIR", "DMDEDUC2"]}
pats = pd.concat([na.block_patterns(coh[c], derived_blocks) for c in coh])
pats.to_csv(OUT / "block_patterns.csv", index=False)
print(pats)

# Giá trị thô của biến thể lực để chốt quy tắc D-19
for c, vs in {"P": ["PAQ650", "PAQ665"], "L": ["PAD790Q", "PAD810Q"]}.items():
    for v in vs:
        if v in coh[c]:
            print(c, v, coh[c][v].describe().round(2).to_dict())

# %% [markdown]
# ## 8. Kiểm tra danh sách biến cấm (K2) và mô tả trôi phân phối P → L

# %%
feat = na.predictor_list() + ["WHTR", "SBP_MEAN", "DBP_MEAN", "SMOKE3", "LTPA_ANY", "GDM"]
bad = na.check_forbidden(feat)
assert not bad, f"K2 fail: {bad}"
dr = na.drift(coh["P"], coh["L"], W["P"], W["L"],
              ["RIDAGEYR", "BMXBMI", "WHTR", "BMXWAIST", "SBP_MEAN", "PAD680", "INDFMPIR", "LTPA_ANY"])
dr.to_csv(OUT / "drift_descriptive.csv", index=False)
print(dr)

# %% [markdown]
# ## 9. Cổng G1–G3

# %%
g = na.gates(ev[ev.cycle == "L"], miss, checks, wds, seqn_overlap)
na.to_json(g, OUT / "gates.json")
print(pd.json_normalize(g).T)
