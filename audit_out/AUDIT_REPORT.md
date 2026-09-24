# Báo cáo audit dữ liệu — lần 1

- **Ngày chạy:** 2026-09-24
- **Code:** `notebooks/01_data_audit.py` + `src/nhanes_audit.py` (đã sửa lỗi đọc số 0, D-29)
- **Dữ liệu:** 20 tệp .xpt tải từ wwwn.cdc.gov; mã băm SHA-256 lưu trong `manifest.csv`
- **Log chạy đầy đủ:** `run_log.txt`
- **Phạm vi:** không huấn luyện mô hình, không tính chỉ số dự báo

## Cổng

| Cổng | Kết quả | Ghi chú |
|---|---|---|
| G1 Toàn vẹn | **Đạt** | SEQN duy nhất trong cả 20 tệp; không có SEQN chung giữa P và L; biến trọng số nhãn có mặt |
| G2 Số sự kiện | **Đạt, sát ngưỡng** | 128 sự kiện (HbA1c ≥6,5) ở L, mốc tối thiểu là 100 → giữ nhãn 6,5% (D-27) |
| G3 Hài hòa | **Đạt về mặt kỹ thuật nhưng có vấn đề** | Hàm kiểm tra chỉ xác nhận biến có mặt. Thực tế: B3 ở L chỉ còn 1 biến; biến thể lực không tương đương giữa P và L (D-24, D-25) |
| G4 Tính mới | Chưa làm | T-2, T-3 |
| G5 Ký duyệt | Chưa làm | D-04, D-15, δ, D-22, D-24–D-26 |

## Cohort

| Bước | P n | L n |
|---|---|---|
| DEMO | 15.560 | 11.933 |
| Tuổi ≥20 | 9.232 | 7.809 |
| Đã khám MEC | 8.544 | 6.064 |
| Có HbA1c | 8.081 | 5.767 |
| Không có thai | 8.005 | 5.730 |
| Không tự báo cáo chẩn đoán ĐTĐ | 6.743 | 4.911 |
| Không dùng thuốc uống hạ đường huyết | **6.644** | **4.826** |

- Nếu loại cả nhóm borderline (DIQ010 = 3): P = 6.458, L = 4.657.
- Có 52 người (P) và 56 người (L) khai "chưa chẩn đoán" nhưng đang dùng thuốc hạ đường huyết. Họ đã bị loại ở bước C8.

## Sự kiện

| Ngưỡng | P sự kiện | P tỷ lệ có trọng số | L sự kiện | L tỷ lệ có trọng số |
|---|---|---|---|---|
| ≥6,5 (chính) | 237 | 2,41% | 128 | 2,29% |
| ≥5,7 (dự phòng) | 2.345 | 27,1% | 1.474 | 26,7% |
| ≥6,35 (thực chất ≥6,4) | 306 | 3,07% | 172 | 3,04% |
| ≥6,65 (thực chất ≥6,7) | 159 | 1,53% | 78 | 1,45% |

- HbA1c được làm tròn đến 0,1, nên các ngưỡng độ nhạy ±0,15 thực chất là 6,4 và 6,7.
- Tỷ lệ có trọng số gần như không đổi giữa P và L.

**Số sự kiện theo phân nhóm ở L** (ngưỡng 6,5):

| Nhóm | Sự kiện |
|---|---|
| Tuổi 20–44 / 45–64 / 65+ | 23 / 49 / 56 |
| Nam / nữ | 67 / 61 |
| Mexican American / Hispanic khác / NH White / NH Black / NH Asian / Khác | 19 / 9 / 64 / 26 / 7 / 3 |
| PIR <1,3 / 1,3–3,5 / >3,5 / thiếu | 23 / 64 / 27 / 14 |

→ Hầu hết nhóm chủng tộc có <30 sự kiện (D-28).

## Trọng số và thiết kế

| | P (WTMECPRP) | L (WTPH2YR) |
|---|---|---|
| Số người có trọng số = 0 (toàn tệp) | 1.260 | 449 |
| Hệ số biến thiên trong cohort | 1,13 | 0,73 |
| Max / trung vị | 20,1 | 7,0 |
| Strata × PSU | 24 strata, 2–3 PSU mỗi strata | 15 strata × 2 PSU |

- Trọng số ở P rất phân tán, ủng hộ D-08 (huấn luyện chính không trọng số).
- L có 15 strata → jackknife với df = 15 (D-13).

## Thiếu tự nhiên

| Biến / khối | P | L |
|---|---|---|
| Huyết áp (B2), cả khối thiếu | 9,6% | 3,2% |
| Vòng eo | 4,1% | 4,0% |
| Các biến nhân trắc khác | ≈1% | ≈1% |
| INDFMPIR | 13,7% | 12,7% |

- SMQ040 thiếu khoảng 60% theo thiết kế (chỉ hỏi người từng hút), SMOKE3 đã xử lý việc này.
- Mẫu thiếu theo khối trong P: không thiếu khối nào 5.969 người; thiếu B2 584; thiếu B1+B2 54; thiếu B1 37.
- **Thiếu tự nhiên cả khối gần như chỉ xảy ra ở B1/B2**, nên các kịch bản S3, S4 hoàn toàn là mô phỏng.

## Biến khác nhau giữa hai chu kỳ

| Biến | P | L | Hệ quả |
|---|---|---|---|
| MCQ300C (tiền sử gia đình ĐTĐ) | có | **không có** | D-25, D-26 |
| RHQ162 (ĐTĐ thai kỳ) | có | **không có** | D-25, D-26 |
| Thể lực giải trí | PAQ650/665 (≥10 phút liên tục) | PAD790Q/810Q (tần suất) | Tỷ lệ "có" 57% → 84%: do cách hỏi → D-24 |
| PAD680 | có | có | Trung bình có trọng số 351 → 362 phút |

**Trôi phân phối** (trung bình có trọng số, P → L): tuổi 46,9 → 47,3; BMI 29,3 → 29,2; WHtR 0,591 → 0,589; HA tâm thu 121,2 → 120,4; PIR 3,17 → 3,09. Trôi nhỏ hơn giả định "đứt gãy đại dịch" của [KT]/[TĐ].

## Giới hạn của audit này

- Mới kiểm "có mặt" và thống kê mô tả. Chưa đọc codebook từng biến để xác nhận cùng câu hỏi và cùng đơn vị (trừ thể lực).
- Chưa kiểm tra có biến chỉ thiết bị đo HbA1c ở mức cá nhân hay không (D-06).
