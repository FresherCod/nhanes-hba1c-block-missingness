# PROJECT_BRIEF

**Cập nhật:** 2026-09-24 (lần 5) — **ĐÃ KHÓA protocol v0.4 và chạy L một lần. Kết quả: `RESULTS_protocol_v0.4.md`. Nhật ký sau khóa: `decision_log_postlock.md`.**

Trạng thái lần 4 (lịch sử):
**Cập nhật:** 2026-09-24 (lần 4) · **Trạng thái:** **protocol v0.4 — ứng viên khóa** (G1–G3 đạt; G4 thiếu toàn văn MEDWACS; G5 còn 3 mục nhỏ) · Đã chạy thử **chỉ trên P** (`dev_out/DEV_REPORT.md`); **L chưa nạp vào mô hình nào**

> **Lần 4:**
> - Chạy thử trên P cho thấy LightGBM quá khớp → đổi learner sang LR spline (D-35).
> - Chỉ số chính là Brier skill, δ = 0,005 (D-36). Giữ nhãn 6,5 (D-37).
> - Đã lấy bảng điểm Bang (D-38).

> **Thay đổi quan trọng lần 3:**
> - Tìm tài liệu cho thấy MEDWACS (J Clin Epidemiol 2026) đã kiểm định mô hình không xét nghiệm trên NHANES 2021–2023. Đóng góp chính giờ chỉ còn là **xử lý thiếu cả khối lúc triển khai**.
> - So sánh chính đổi thành che khối (M-AUG) vs mô hình con theo mẫu thiếu (M-PS) (D-30).
> - Xem `protocol_v0.3.md`, `literature_extraction.md`, `search_log.md`.
> - Phần "một câu" và "vì sao đáng làm" bên dưới là của v0.2; chỗ nào khác thì `protocol_v0.3.md` được ưu tiên.

## Một câu
Kiểm tra xem huấn luyện có che khối biến có giúp một mô hình nhẹ (LightGBM), chỉ dùng biến không xét nghiệm, dự đoán HbA1c ≥ 6,5% ở người trưởng thành chưa được chẩn đoán ĐTĐ ổn định hơn khi thiếu cả một khối thông tin lúc sử dụng hay không. Phát triển trên NHANES 2017–03/2020, kiểm định trên 2021–2023, đánh giá có trọng số khảo sát.

## Vì sao đáng làm (đóng góp đề xuất, chưa kiểm chứng xong)
Bài gần nhất tìm được là arXiv:2606.16056 (*Beyond the Blood Draw*, 2026). Theo trích xuất tự động, **chưa đọc tay**, bài này:
- gộp NHANES 2017–2023 rồi chia ngẫu nhiên;
- có nhãn gồm cả người đã chẩn đoán, với ngưỡng 5,7%;
- không dùng trọng số;
- không xét thiếu theo khối.

Đề tài khác ở bốn điểm:
1. Chỉ người chưa chẩn đoán.
2. Kiểm định theo thời gian qua giai đoạn đại dịch.
3. Chỉ số có trọng số, với CI theo thiết kế.
4. Thiếu theo khối là biến can thiệp chính.

"Survey-aware ML" **không** được coi là đóng góp mới: Matabuena và cs. 2024 đã làm (D-08).

## Thiết kế một dòng
Cohort P → L · nhãn LBXGH ≥ 6,5 · 4 khối có thể che (nhân trắc, huyết áp, tiền sử, lối sống/KT–XH) · M-AUG vs M-BASE · chỉ số chính ΔBrierʷ trung bình qua S1–S5 · CI jackknife theo PSU. Chi tiết: `protocol_v0.2.md`.

## Tệp trong dự án
| Tệp | Vai trò |
|---|---|
| `integration_A4.md` | Bảng tích hợp đầu ra AI với nguồn gốc |
| `protocol_v0.2.md` | Protocol hiện hành (chưa khóa) |
| `decision_log.md` | Mọi quyết định thiết kế (D-01 đến D-21) |
| `notebooks/01_data_audit.ipynb` (+ `.py`) | Audit dữ liệu tối thiểu, **không có mô hình** |
| `src/nhanes_audit.py` | Hàm dựng cohort và audit dùng chung cho P và L |
| 3 file .docx | Đầu ra AI ban đầu: chỉ tham khảo, không làm căn cứ |

## Cổng trước khi khóa protocol
- G1: toàn vẹn dữ liệu
- G2: ≥100 sự kiện ở L
- G3: hài hòa biến
- G4: tính mới đã kiểm chứng
- G5: Vincent ký các mục chưa chốt

## Nhiệm vụ tiếp theo (nhỏ nhất, đúng chỗ thiếu)
| ID | Việc | Giải quyết | Ai | Ước lượng |
|---|---|---|---|---|
| T-1 | Chạy `01_data_audit` (tải khoảng 20 tệp .xpt công khai từ CDC) | G1, G2, G3; xác nhận D-05, D-06, D-07 | Claude/Vincent, cần Vincent đồng ý tải | < 15 phút |
| T-2 | Tìm có hệ thống, lưu `search_log.md` (PubMed, arXiv, medRxiv, Google Scholar; ngày tìm; số kết quả; lý do loại). Truy vấn gợi ý: `NHANES AND (undiagnosed diabetes OR HbA1c) AND (machine learning OR prediction) AND (missing* OR temporal OR "survey weight*")` | G4, D-10 | Vincent | 1–2 giờ |
| T-3 | Đọc tay toàn văn arXiv:2606.16056, Liu 2025 (JMIR AI), Bang 2009, Casacchia 2024, Matabuena (arXiv:2403.19752). Điền 8 trường: cohort, nhãn, chu kỳ, split, trọng số, thiếu, hiệu chuẩn, ngưỡng | G4, D-09, D-14 | Vincent (Claude đọc nếu có PDF trong thư mục) | 2–3 giờ |
| T-4 | Ánh xạ từng mục của ADA risk test (Bang 2009) sang biến P và L | D-14 | Sau T-1 và T-3 | 30 phút |
| T-5 | Quyết định: xử lý DIQ010 = 3, độ nhạy mục tiêu 80%, biên δ, quy tắc thể lực | G5 | Vincent + người hướng dẫn | 1 buổi họp |

## Không làm lúc này
Huấn luyện mô hình trên L; tuning diện rộng; thêm MICE, MLP, đa nhiệm, Tầng 2; viết kết quả giả định.
