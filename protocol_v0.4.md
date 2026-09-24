# Protocol v0.4 — ỨNG VIÊN KHÓA (chưa khóa)

- **Phiên bản:** 0.4 (2026-09-24).
- **Kế thừa** `protocol_v0.3.md`. Mục nào không nhắc lại ở đây thì giữ nguyên v0.3.
- **Thay đổi:** D-35 (learner LR), D-36 (Brier skill, δ = 0,005), D-37 (giữ nhãn 6,5), D-38 (điểm Bang), D-39 (chỉ báo khối).
- **Minh bạch:** D-35 và D-36 được quyết định **sau khi** chạy thử trên dữ liệu phát triển P (`dev_out/DEV_REPORT.md`). Tập L (2021–2023) **chưa được nạp** vào bất kỳ mô hình nào; lần duy nhất L được đọc là trong audit mô tả (tỷ lệ nhãn, thiếu dữ liệu, phân phối biến).

## 1. Câu hỏi chính
Không đổi so với v0.3. Learner là LR spline có phạt.

## 2. So sánh chính

| | |
|---|---|
| Can thiệp | **M-AUG**: một LR spline, huấn luyện trên P gốc + 1 bản sao che ngẫu nhiên một kịch bản S1–S5, có 4 chỉ báo khối bị che |
| Đối chứng chính | **M-PS**: 6 LR spline (S0–S5), mỗi mô hình bỏ hẳn các khối tương ứng |
| Chỉ số | Brier skillʷ = 1 − Brierʷ / [p̄ʷ(1 − p̄ʷ)], tính trên L, trọng số WTPH2YR |
| Estimand chính | Δ = skill(M-AUG) − skill(M-PS), trung bình không trọng số qua S1–S5 |
| δ | **0,005** |
| Kết luận định trước | (a) CI 95% của Δ nằm trọn trong (−0,005; +0,005) → **tương đương thực tế**. (b) Cận dưới CI > 0 → M-AUG tốt hơn. (c) Cận trên CI < 0 → M-PS tốt hơn. (d) Các trường hợp khác → không kết luận được |
| Điều kiện phụ tại S0 | skill(M-AUG) − skill(M-PS) có cận dưới CI > −0,005 (không kém hơn) |
| Phụ | M-BASE (LR không che); LightGBM (M-AUG/M-PS/M-BASE, lưới ≤12); điểm Bang ≥5; nhãn 5,7%; loại borderline; ngưỡng HbA1c 6,4/6,7 |

## 3. Tuning
- LR: C ∈ {0,03; 0,1; 0,3; 1}, spline 4 knot bậc 3 cố định.
- Chọn C theo **log loss có trọng số** trên OOF GroupKFold 5 fold (nhóm = strata × PSU) của P. Chọn riêng cho M-AUG và cho từng mô hình con của M-PS.
- 5 seed (0–4) cho phần ngẫu nhiên của augmentation; kết quả chính = trung bình dự đoán của 5 seed.

## 4. Kết quả trên L — thứ tự chạy khi mở khóa
1. Tạo `LOCK_protocol_v0.4.json` gồm: mã băm SHA-256 của protocol, `decision_log.md`, `src/*.py`, cấu hình, và commit (nếu dùng git).
2. Huấn luyện lại mọi mô hình trên **toàn bộ P** với C đã chọn. Lưu mô hình và mã băm.
3. Nạp L một lần; dự đoán S0–S7; lưu file dự đoán kèm mã băm.
4. Tính chỉ số và CI JK2 (15 strata) theo mục 9 của v0.2.
5. Không chạy lại bước 2–4 với bất kỳ thay đổi nào. Mọi phân tích thêm sau đó được gắn nhãn hậu kiểm.

## 5. Mục còn mở (G5) trước khi khóa — **ĐÃ ĐÓNG** ngày 2026-09-24

Đóng theo D-40 (G4 đạt), D-41, D-42, D-43 (Claude, theo ủy quyền toàn bộ của Vincent). Bảng dưới giữ lại để làm lịch sử.

| Mục | Đề xuất mặc định | Cần ai |
|---|---|---|
| D-22 người thiếu DIQ010 (2 người ở L) | Loại | Vincent |
| D-06 độ nhạy thiết bị HbA1c | Làm phân tích phụ ngưỡng 6,4/6,7 như v0.3 | Vincent |
| Mô hình con cho S6 | Huấn luyện thêm, chỉ dùng cho phân tích phụ | Vincent |
| G4: toàn văn MEDWACS | Cần PDF | **Vincent cung cấp** |
| G4: sàng lọc 73 kết quả Q2 | Claude làm được | Claude |
