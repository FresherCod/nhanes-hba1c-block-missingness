# HẬU KIỂM đợt 3A (sau khóa protocol v0.4; xem addendum_posthoc_round3_20261014.md). Không sửa file đã khóa.
# Câu hỏi: với nhãn HbA1c >=5,7% (1.474 sự kiện ở L), khối nào ngoài nhân trắc (B1) có thông tin,
#          và M-AUG so với M-PS khác nhau thế nào TỪNG kịch bản (không chỉ trung bình S1-S5)?
# Chỉ dùng mô hình LR57-* đã huấn luyện và khóa trong final_out/models_P.pkl. KHÔNG huấn luyện lại, KHÔNG chọn gì trên L.
# Chạy từ thư mục gốc: python notebooks/10a_posthoc_label57_by_scenario.py
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import final_pipeline as fp

sys.stdout.reconfigure(encoding="utf-8")
RAW, OUT = ROOT / "data" / "raw", ROOT / "posthoc_out"
fp.verify_lock(ROOT, ROOT / "LOCK_protocol_v0.4.json")
print("LOCK OK")

B = fp.load_pickle(ROOT / "final_out" / "models_P.pkl")
L = fp.cohort("L", RAW, 5.7).reset_index(drop=True)
y = L.y.values
print("L nhan 5.7: n =", len(L), "su kien =", int(y.sum()))
MODELS = {"AUG": B["models"]["LR57-AUG"], "PS": B["models"]["LR57-PS"], "BASE": B["models"]["LR57-BASE"]}
SC = list(fp.SCEN)  # S0..S6
pred = {m: {s: mod.predict(L, fp.SCEN[s]) for s in SC} for m, mod in MODELS.items()}


def skill(p, w):
    pb = np.average(y, weights=w)
    return 1 - np.average((p - y) ** 2, weights=w) / (pb * (1 - pb))


# ---- kiểm tra tái lập: phải khớp final_out/L_table_LR_label57.csv (kết quả đã khóa)
ref = {(r["model"], r["scenario"]): float(r["skill"])
       for r in csv.DictReader(open(ROOT / "final_out" / "L_table_LR_label57.csv", encoding="utf-8"))}
w0 = L["w"].values
worst = max(abs(skill(pred[m][s], w0) - ref[(f"LR57-{m}", s)]) for m in MODELS for s in SC)
print(f"Kiem tra tai lap so voi L_table_LR_label57.csv: sai lech toi da = {worst:.2e}")
assert worst < 1e-9, "Khong khop ket qua da khoa: DUNG, khong dien giai so lieu moi"


def fn(w):
    sk = {(m, s): skill(pred[m][s], w) for m in MODELS for s in SC}
    out = {}
    for m in MODELS:
        for s in SC:
            out[f"skill_{m}_{s}"] = sk[(m, s)]
    for s in SC[1:]:
        out[f"drop_AUG_{s}"] = sk[("AUG", "S0")] - sk[("AUG", s)]          # mất skill so với đủ dữ liệu
        out[f"AUG-PS_{s}"] = sk[("AUG", s)] - sk[("PS", s)]
        out[f"AUG-BASE_{s}"] = sk[("AUG", s)] - sk[("BASE", s)]
    for tag, grp in {"S1-S5": ["S1", "S2", "S3", "S4", "S5"], "B1 (S1,S5)": ["S1", "S5"],
                     "khong B1 (S2,S3,S4)": ["S2", "S3", "S4"]}.items():
        out[f"AUG-PS_mean[{tag}]"] = float(np.mean([sk[("AUG", s)] - sk[("PS", s)] for s in grp]))
        out[f"AUG-BASE_mean[{tag}]"] = float(np.mean([sk[("AUG", s)] - sk[("BASE", s)] for s in grp]))
    return out


res = fp.with_ci(fn, L)
(OUT / "posthoc3a_label57_by_scenario.json").write_text(
    json.dumps({"label": "HAU KIEM dot 3A (nhan >=5.7) - khong thuoc protocol v0.4", "results": res},
               ensure_ascii=False, indent=2), encoding="utf-8")
with open(OUT / "posthoc3a_label57_by_scenario.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["quantity", "est", "lo95", "hi95", "within_pm_delta"])
    for k, v in res.items():
        inside = (v["lo"] > -fp.DELTA and v["hi"] < fp.DELTA) if k.startswith("AUG-") else ""
        wr.writerow([k, f"{v['est']:.5f}", f"{v['lo']:.5f}", f"{v['hi']:.5f}", inside])


def row(k):
    v = res[k]
    return f"{v['est']:8.4f} [{v['lo']:8.4f}; {v['hi']:8.4f}]"


print("\nBrier skill (nhan >=5.7), co trong so khao sat, CI JK2")
print("scenario |  M-AUG    |  M-PS     |  M-BASE   | mat skill M-AUG vs S0")
for s in SC:
    drop = row(f"drop_AUG_{s}") if s != "S0" else "-"
    print(f"{s:8s} | {res[f'skill_AUG_{s}']['est']:.4f}    | {res[f'skill_PS_{s}']['est']:.4f}    | "
          f"{res[f'skill_BASE_{s}']['est']:.4f}    | {drop}")
print("\nM-AUG - M-PS (bien tuong duong +/-%.3f; dung de so sanh, khong phai quy tac dinh truoc cho nhan nay)" % fp.DELTA)
for s in SC[1:]:
    print(f"  {s}: {row(f'AUG-PS_{s}')}")
for tag in ["S1-S5", "B1 (S1,S5)", "khong B1 (S2,S3,S4)"]:
    print(f"  trung binh {tag}: {row(f'AUG-PS_mean[{tag}]')}")
print("\nM-AUG - M-BASE")
for tag in ["S1-S5", "B1 (S1,S5)", "khong B1 (S2,S3,S4)"]:
    print(f"  trung binh {tag}: {row(f'AUG-BASE_mean[{tag}]')}")
print("\nDoi chieu: Bang 4 cua ban thao co M-AUG - M-PS (nhan >=5.7, trung binh S1-S5) = -0.0015 [-0.0032; 0.0001]")
print("Da ghi: posthoc_out/posthoc3a_label57_by_scenario.csv va .json")
