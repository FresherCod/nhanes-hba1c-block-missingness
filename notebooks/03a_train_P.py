# Giai đoạn A — CHỈ P. Tuning, huấn luyện cuối, ngưỡng, hiệu chuẩn lại. Không nạp L.
# Chạy từ thư mục gốc: python notebooks/03a_train_P.py
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import final_pipeline as fp

RAW, OUT = ROOT / "data" / "raw", ROOT / "final_out"
OUT.mkdir(exist_ok=True)
fp.check_forbidden()
t0 = time.time()

coh = fp.cohort("P", RAW, threshold=6.5)
print("P:", len(coh), "sự kiện:", int(coh.y.sum()))
log = []
bundle = {"config": {}, "models": {}, "thresholds": {}, "recal": {}}

for learner in ["LR", "LGB"]:
    tn = fp.tune(coh, learner, log)
    ch, oo = tn["chosen"], tn["oof"]
    bundle["config"][learner] = {"BASE": ch["BASE"], "AUG": ch["AUG"], "PS": ch["PS"]}
    print(learner, "chọn:", bundle["config"][learner], f"({time.time()-t0:.0f}s)")
    y, w = coh.y.values, coh.w.values
    oof_s0 = {"BASE": oo["BASE"]["S0"], "AUG": oo["AUG"]["S0"], "PS": oo["PS"]["S0"]}
    for meth, p in oof_s0.items():
        key = f"{learner}-{meth}"
        bundle["thresholds"][key] = fp.sens_threshold(y, p, w)
        bundle["recal"][key] = fp.recalibrator(y, p, w).tolist()
        print(" ", key, "OOF S0", {k: round(v, 4) for k, v in fp.metrics(y, p, w).items()
                                   if k in ("skill", "auc", "slope")},
              "ngưỡng", round(bundle["thresholds"][key], 4))
    bundle["models"][f"{learner}-BASE"] = fp.Base(learner, ch["BASE"]).fit(coh)
    bundle["models"][f"{learner}-AUG"] = fp.AugEnsemble(learner, ch["AUG"]).fit(coh)
    bundle["models"][f"{learner}-PS"] = fp.PatternSub(learner, ch["PS"]).fit(coh)

# Phụ: huấn luyện có trọng số (LR, cùng siêu tham số)
c = bundle["config"]["LR"]
bundle["models"]["LRw-AUG"] = fp.AugEnsemble("LR", c["AUG"], weighted=True).fit(coh)
bundle["models"]["LRw-PS"] = fp.PatternSub("LR", c["PS"], weighted=True).fit(coh)

# Phụ: nhãn HbA1c ≥5,7 (LR, tuning riêng)
coh57 = fp.cohort("P", RAW, threshold=5.7)
log57 = []
tn57 = fp.tune(coh57, "LR", log57)
bundle["config"]["LR57"] = tn57["chosen"]
bundle["models"]["LR57-AUG"] = fp.AugEnsemble("LR", tn57["chosen"]["AUG"]).fit(coh57)
bundle["models"]["LR57-PS"] = fp.PatternSub("LR", tn57["chosen"]["PS"]).fit(coh57)
bundle["models"]["LR57-BASE"] = fp.Base("LR", tn57["chosen"]["BASE"]).fit(coh57)
log += [dict(r, label="5.7") for r in log57]

# Ngưỡng Bang cố định ≥5 (không chọn lại)
bundle["thresholds"]["BANG"] = 5
fp.save_pickle(bundle, OUT / "models_P.pkl")
pd.DataFrame(log).to_csv(OUT / "tuning_log_P.csv", index=False)
cfg = {k: v for k, v in bundle.items() if k in ("config", "thresholds", "recal")}
(OUT / "config_P.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2, default=str),
                                   encoding="utf-8")
print(f"Xong giai đoạn A ({time.time()-t0:.0f}s)")
