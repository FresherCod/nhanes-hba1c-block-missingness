# Báo cáo chạy thử phát triển — CHỈ dữ liệu P (2017–03/2020)

- **Ngày:** 2026-09-24.
- **Code:** `notebooks/02_dev_P_only.py` (LightGBM), `notebooks/02b_dev_LR_P_only.py` (LR).
- **Log:** `dev_checks.json`, `summary_P_seed0.csv`, `dev_LR_P_jackknife.txt`.
- **Không phải kết quả nghiên cứu:** OOF 5 fold theo PSU, 1 seed, tham số cố định, không tuning. **L chưa được nạp** (K10 đã xác nhận).
- **Mục đích duy nhất:** kiểm tra pipeline, các chốt rò rỉ, và cung cấp căn cứ để chọn learner, chỉ số chính, δ **trước khi** khóa protocol. Việc chọn dựa trên kết quả này được ghi công khai ở D-35 đến D-37.

## Kiểm tra rò rỉ

| Kiểm tra | Kết quả |
|---|---|
| K2 danh sách biến cấm | Đạt |
| K3 PSU không rò giữa train/val; bản sao augmentation giữ nhóm train | Đạt (assert) |
| K6 hoán vị nhãn | AUROC 0,48 → đạt |
| K7 biến đơn lẻ mạnh nhất | WHtR, AUROC 0,71 → đạt (<0,85) |
| K9 mô hình con không thấy cột khối bị bỏ | Đạt (assert) |
| K10 L bị khóa | Đạt |

## Phát hiện 1 — LightGBM với tham số cố định quá khớp (237 sự kiện)

| Mô hình (S0, OOF P) | AUROCʷ | Brierʷ | Brier skillʷ | Calibration slope |
|---|---|---|---|---|
| LR spline (C = 0,1) | 0,808 | 0,02270 | **0,033** | 1,38 |
| LightGBM tham số cố định | 0,754 | 0,02358 | **−0,005** (kém hơn đoán bằng tỷ lệ nền) | 0,58 |

Brier null (tỷ lệ nền) = 0,02348. Với tỷ lệ 2,4%, Brier tuyệt đối gần như không phân biệt được các mô hình. Vì vậy δ = 0,002 Brier đề nghị ở v0.2/v0.3 không dùng được.

## Phát hiện 2 — So sánh chính bằng LR (jackknife theo PSU trên P, 24 strata)

| Ước lượng (Brier skillʷ, trung bình S1–S5) | HbA1c ≥6,5 (237 ca) | HbA1c ≥5,7 (2.345 ca) |
|---|---|---|
| M-AUG − M-PS | −0,0014 [−0,0031; 0,0003] | −0,0023 [−0,0042; −0,0004] |
| M-AUG − M-BASE | +0,0035 [0,0010; 0,0059] | +0,0087 [0,0035; 0,0140] |
| M-BASE mất khi thiếu khối (S0 − S1…S5) | 0,0108 [0,0063; 0,0153] | 0,0261 [0,0198; 0,0324] |
| Brier skill của M-PS tại S0 | 0,033 | 0,178 |

## Diễn giải (chỉ để thiết kế, không để kết luận)

- **Hiệu ghép cặp rất chính xác** (SE ≈ 0,001), ngay cả ở ngưỡng 6,5 → giữ nhãn 6,5 không làm mất khả năng so sánh chính.
- **Thiếu khối có ý nghĩa thực tế:** mô hình không xử lý thiếu mất khoảng 1/3 Brier skill ở ngưỡng 6,5.
- **Trên P, M-PS nhỉnh hơn M-AUG một chút.** Kết quả trên L có thể khác, và protocol phải cho phép mọi hướng kết quả.
