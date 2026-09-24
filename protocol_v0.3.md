# Protocol v0.3 — CHƯA KHÓA

Tên làm việc: *Xử lý thiếu cả khối thông tin lúc sử dụng trong mô hình sàng lọc HbA1c đạt ngưỡng từ biến không xét nghiệm: che khối khi huấn luyện so với mô hình con theo mẫu thiếu, kiểm định theo thời gian trên NHANES*

- **Phiên bản:** 0.3 (2026-09-24). Thay đổi so với v0.2 theo D-04, D-15, D-24, D-25, D-30, D-32, D-33 (Vincent duyệt qua chat 2026-09-24). v0.2 giữ nguyên làm lịch sử.
- **Căn cứ:** `audit_out/AUDIT_REPORT.md`, `literature_extraction.md`, `search_log.md`.
- **Ký hiệu:** `[CHƯA CHỐT]` = còn mở; `[AUDIT]` = đã xác nhận bằng dữ liệu (có ghi số).

---

## 0. Định vị tính mới (sau T-2/T-3)

| Đặc điểm thiết kế | Đã có trong tài liệu | Vai trò trong đề tài |
|---|---|---|
| Chỉ người chưa chẩn đoán | Liu 2025, Bang 2009 | Đặc điểm thiết kế |
| Kiểm định theo thời gian sang 2021–2023 | MEDWACS 2026 (nhãn tiền ĐTĐ + ĐTĐ) | Đặc điểm thiết kế |
| Đánh giá có trọng số | Bang 2009, Casacchia 2024 | Đặc điểm thiết kế |
| **Thiếu cả khối lúc triển khai: che khối khi huấn luyện so với mô hình con theo mẫu thiếu** | Không tìm thấy trong sàng lọc ĐTĐ (search_log lần 1) | **Đóng góp chính** |

Chỉ viết "chưa có nghiên cứu nào" sau khi hoàn thành các việc còn lại trong search_log và đọc toàn văn MEDWACS (G4).

## 1. Câu hỏi chính

Ở người trưởng thành NHANES chưa tự báo cáo chẩn đoán ĐTĐ, khi một khối thông tin không xét nghiệm bị thiếu lúc sử dụng, **một mô hình duy nhất huấn luyện có che khối (M-AUG)** có dự đoán HbA1c ≥6,5% tốt ngang hoặc hơn **bộ mô hình con riêng cho từng mẫu thiếu (M-PS)** không? Phát triển trên 2017–03/2020, đánh giá trên 2021–2023, bằng Brier score có trọng số khảo sát.

## 2. So sánh chính (D-30)

| | |
|---|---|
| Can thiệp | **M-AUG**: một LightGBM, huấn luyện trên dữ liệu gốc + bản sao đã che khối (mục 6) |
| Đối chứng chính | **M-PS**: 6 LightGBM, mỗi mô hình ứng với một kịch bản S0–S5, huấn luyện trên toàn bộ P với các khối tương ứng bị bỏ (mô hình con bỏ biến). Lúc dự đoán, chọn mô hình con khớp với mẫu thiếu |
| Estimand chính | Δ = Brierʷ(M-AUG) − Brierʷ(M-PS) trên L, trung bình không trọng số qua S1–S5 |
| Diễn giải | Δ < 0 và CI 95% không chứa 0 → M-AUG tốt hơn. CI nằm trọn trong (−δ, +δ) → tương đương thực tế (M-AUG gọn hơn, chỉ một mô hình). Còn lại → không kết luận được |
| δ | `[CHƯA CHỐT]`, đề nghị 0,002 Brier; phải chốt trước khi mở L |
| Đối chứng phụ | M-BASE (LightGBM không che, NaN tự nhiên); LR (spline + chỉ báo thiếu); điểm Bang 2009 (D-33) |

## 3. Cohort và nhãn `[AUDIT]`

Dùng một hàm `build_cohort` cho cả P và L. Các bước:
1. Tuổi ≥20.
2. Đã khám MEC.
3. Có LBXGH.
4. Trọng số nhãn >0.
5. RIDEXPRG ≠ 1.
6. DIQ010 ∉ {1, 7, 9} và không thiếu `[CHƯA CHỐT: D-22, ảnh hưởng 2 người ở L]`.
7. DIQ070 ≠ 1.

**Borderline** (DIQ010 = 3) **giữ lại**; phân tích độ nhạy loại ra (D-04 ☑).

| | P | L |
|---|---|---|
| n | 6.644 | 4.826 |
| Sự kiện HbA1c ≥6,5 | 237 | 128 |
| Tỷ lệ có trọng số | 2,41% | 2,29% |
| n nếu loại borderline | 6.458 | 4.657 |

**Nhãn** = 1{LBXGH ≥ 6,5}. Tên gọi: "HbA1c đạt ngưỡng ĐTĐ ở người chưa được chẩn đoán".

**Độ nhạy nhãn** (D-06, `[CHƯA CHỐT]`): ngưỡng ≥6,4 và ≥6,7. HbA1c được làm tròn 0,1, và ở ngưỡng ≥6,7 chỉ có 78 sự kiện nên chỉ báo cáo mô tả.

## 4. Biến dự báo (D-24 ☑, D-25 ☑)

| Khối | Biến dùng trong mô hình | Nguồn | Có thể che? |
|---|---|---|---|
| Lõi | tuổi, giới, RIDRETH3 | DEMO | Không |
| B1 Nhân trắc | BMXBMI, BMXWAIST, BMXHT, BMXWT, WHtR | BMX | Có |
| B2 Huyết áp đo | SBP_MEAN, DBP_MEAN | BPXO | Có |
| B3 Tiền sử | BPQ020 (từng được báo THA) | BPQ | Có |
| B4 Lối sống/KT–XH | SMOKE3, PAD680, INDFMPIR, DMDEDUC2 | SMQ, PAQ, DEMO | Có |

**Đã bỏ vì không có hoặc không tương đương ở L** `[AUDIT]`:
- MCQ300C (tiền sử gia đình): không có trong MCQ_L.
- RHQ162 (ĐTĐ thai kỳ): không có trong RHQ_L.
- Thể lực giải trí: câu hỏi đổi, tỷ lệ "có" nhảy từ 57% lên 84%.

**Cấm dùng:** như v0.2 (D-17).

## 5. Chia dữ liệu, tuning, seed

Giữ nguyên như v0.2, với bổ sung:
- **Cùng lưới siêu tham số (≤12 cấu hình)** cho M-AUG và **cho từng mô hình con** của M-PS, chọn bằng GroupKFold theo (SDMVSTRA, SDMVPSU) trên P.
- **Khóa L trong code:** hàm nạp L chỉ chạy khi có file `LOCK_protocol_v*.json` chứa mã băm của protocol và cấu hình.

## 6. Kịch bản thiếu

- **Kịch bản đánh giá:** S0–S7 như v0.2 (B3 giờ chỉ có 1 biến).
- **M-AUG:** mỗi dòng train được thêm 1 bản sao, gán ngẫu nhiên một mẫu thiếu trong {S1…S5}. Làm sau khi chia fold, bản sao cùng nhóm với dòng gốc. Có 4 biến chỉ báo khối bị che `[CHƯA CHỐT: có dùng biến chỉ báo không — đề nghị có]`.
- **M-PS:** chỉ có mô hình con cho S0–S5. S6 (B3+B4) không khớp mô hình con nào. `[CHƯA CHỐT]` quy tắc xử lý: đề nghị huấn luyện thêm một mô hình con cho S6, chỉ dùng trong phân tích phụ. Như vậy S6 không còn là "mẫu chưa thấy" với M-PS; cần ghi rõ điều này khi so sánh.

## 7. Hiệu chuẩn

Như v0.2. Bổ sung D-32: với 128 sự kiện, calibration slope và intercept **chỉ mô tả**; không dùng để kết luận so sánh.

## 8. Chỉ số và ngưỡng

- Chỉ số: như v0.2.
- **Ngưỡng (D-15 ☑):** mỗi phương pháp có một ngưỡng xác suất, chọn trên OOF của P tại S0 sao cho độ nhạy có trọng số = 80%. Ngưỡng này áp nguyên cho mọi kịch bản và cho L.
- **Điểm Bang:** dùng điểm cắt gốc ≥5, không chọn lại.

## 9–11. Độ bất định, trọng số, kiểm tra rò rỉ

Như v0.2 (JK2 trên L với 15 strata `[AUDIT]`; P: 24 strata, 2–3 PSU `[AUDIT]`). Bổ sung:
- **K9:** mỗi mô hình con của M-PS **không** được thấy cột của khối bị bỏ (kiểm bằng assert trên danh sách cột).
- **K10:** L không được nạp nếu chưa có file LOCK.

## 12. Cổng

| Cổng | Trạng thái |
|---|---|
| G1 | **Đạt** `[AUDIT]` |
| G2 | **Đạt** (128 ≥ 100) `[AUDIT]` |
| G3 | **Đạt sau D-24, D-25** |
| G4 | **Đạt một phần**: còn thiếu toàn văn MEDWACS; sàng lọc Q2 chưa xong |
| G5 | Còn mở: δ; D-22; D-06; biến chỉ báo khối trong M-AUG; fallback của M-PS cho S6; bảng điểm Bang (T-4) |

**Tiêu chí dừng/đổi hướng sau khi chạy:** như v0.2, và thêm một điều: nếu MEDWACS hoặc bài nào khác trong phần tìm tiếp đã so sánh chiến lược thiếu khối lúc triển khai cho sàng lọc ĐTĐ, thì đổi khung thành nghiên cứu kiểm định độc lập (ghi log, không âm thầm).

## 13. Giới hạn

Như v0.2, và thêm:
- Mất tiền sử gia đình ĐTĐ ở L. Đây là yếu tố dự báo mạnh (Liu 2025: 48,8% ở nhóm ĐTĐ chưa chẩn đoán so với 36,2%), nên hiệu năng tuyệt đối sẽ thấp hơn các bài dùng biến này.
- Kịch bản thiếu S3, S4 hoàn toàn là mô phỏng: trong dữ liệu, thiếu tự nhiên cả khối chỉ xảy ra ở B1/B2.
