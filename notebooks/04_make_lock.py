# Tạo LOCK_protocol_v0.4.json sau giai đoạn A và dry-run. Chạy từ thư mục gốc.
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import final_pipeline as fp

LOCK = ROOT / "LOCK_protocol_v0.4.json"
if LOCK.exists():
    raise SystemExit("LOCK đã tồn tại — không ghi đè")
files = [ROOT / "protocol_v0.4.md", ROOT / "protocol_v0.3.md", ROOT / "decision_log.md",
         *sorted((ROOT / "src").glob("*.py")),
         ROOT / "notebooks" / "03a_train_P.py", ROOT / "notebooks" / "03b_evaluate_L.py",
         ROOT / "final_out" / "models_P.pkl", ROOT / "final_out" / "config_P.json"]
lock = {"protocol": "v0.4", "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "authorized_by": "Vincent (ủy quyền toàn bộ cho Claude, chat 2026-09-24)",
        "L_loaded_into_models_before_lock": False,
        "files": fp.lock_manifest(ROOT, files)}
LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(lock, ensure_ascii=False, indent=2))
