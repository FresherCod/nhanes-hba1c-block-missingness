# Kết quả — protocol v0.4 (đã khóa)

- **Khóa:** `LOCK_protocol_v0.4.json`, tạo lúc 2026-09-24 10:56:12. Sau khi chạy, đã kiểm lại mã băm: mọi file đã khóa không đổi.
- **Chạy trên L (NHANES 08/2021–08/2023):** một lần, 10:56:22–10:57:54. Mã băm dự đoán: `f329876f…f14361` (`final_out/L_predictions.csv`).
- **Dữ liệu và thiết kế:**
  - Phát triển: NHANES 2017–03/2020, n = 6.644, 237 sự kiện.
  - Kiểm định theo thời gian: n = 4.826, 128 sự kiện, 15 strata.
  - Nhãn: HbA1c ≥6,5% ở người trưởng thành chưa tự báo cáo chẩn đoán ĐTĐ.
  - Chỉ số và trọng số: Brier skill có trọng số khảo sát (WTPH2YR); CI 95% jackknife JK2, t với df = 15.
- **Số liệu gốc:** `final_out/L_results.json`, `final_out/L_table_*.csv`.

## 1. Kết quả chính

| Estimand | Ước lượng | CI 95% | Kết luận định trước (δ = 0,005) |
|---|---|---|---|
| Δ Brier skill (M-AUG − M-PS), trung bình S1–S5 | **−0,0006** | −0,0023 đến 0,0012 | **Tương đương thực tế** |
| Δ tại S0 (không thiếu dữ liệu) | +0,0004 | −0,0009 đến 0,0017 | Không kém hơn: **đạt** |

**Diễn giải:** với LR spline, một mô hình duy nhất huấn luyện có che khối cho kết quả **tương đương** bộ 6 mô hình con riêng cho từng mẫu thiếu. Ở mọi kịch bản, CI đều nằm sát 0, bên trong biên ±0,005.

**Hệ quả thực tiễn:** triển khai chỉ cần một mô hình mà không mất hiệu năng. Nghiên cứu **không** cho thấy che khối tốt hơn mô hình con.

## 2. Vì sao câu hỏi này quan trọng: cách xử lý thiếu ngây thơ gây hại rõ

| So sánh (Brier skill, trung bình S1–S5) | Ước lượng | CI 95% |
|---|---|---|
| M-BASE (không xử lý thiếu) mất skill khi thiếu khối | 0,018 | 0,011 đến 0,026 |
| M-AUG − M-BASE | +0,009 | 0,006 đến 0,012 |
| M-PS − M-BASE | +0,009 | 0,006 đến 0,013 |

Khi thiếu nhân trắc (S1), M-BASE:
- hiệu chuẩn lệch nặng: O/E 0,60, CITL −0,53;
- chuyển 55% dân số đi xét nghiệm (M-AUG: 32%);
- có Brier skill âm.

## 3. Hiệu năng từng kịch bản (LR, có trọng số, trên L)

| Kịch bản | M-AUG skill [CI] | M-AUG AUROC | M-PS skill | M-PS AUROC | M-BASE skill |
|---|---|---|---|---|---|
| S0 đủ dữ liệu | 0,035 [0,014; 0,057] | 0,816 | 0,035 | 0,811 | 0,035 |
| S1 thiếu nhân trắc | 0,011 | 0,723 | 0,011 | 0,729 | −0,008 |
| S2 thiếu huyết áp | 0,035 | 0,815 | 0,033 | 0,815 | 0,034 |
| S3 thiếu tiền sử | 0,038 | 0,821 | 0,038 | 0,826 | 0,035 |
| S4 thiếu lối sống/KT–XH | 0,034 | 0,819 | 0,037 | 0,822 | 0,033 |
| S5 thiếu nhân trắc + HA | 0,010 | 0,703 | 0,011 | 0,713 | −0,010 |

**Khối quyết định là nhân trắc (B1).** Thiếu B1 làm mất khoảng 2/3 skill dù xử lý tốt nhất. Các khối B2, B3, B4 gần như không ảnh hưởng.

**Hàm ý thực tiễn:** chương trình sàng lọc nên ưu tiên đo cân nặng, chiều cao và vòng eo hơn là thu thập thêm câu hỏi.

## 4. Hiệu chuẩn và ngưỡng (LR, S0, trên L)

**Hiệu chuẩn:**

| Mô hình | CITL | Slope [CI] | O/E | ICI |
|---|---|---|---|---|
| M-AUG | −0,10 | 1,13 [0,92; 1,35] | 0,91 | 0,005 |
| M-PS | −0,13 | 1,20 [0,97; 1,43] | 0,89 | 0,003 |

Mô hình ước lượng nguy cơ hơi cao, khoảng 10%, phù hợp với tỷ lệ nền ở L thấp hơn P (2,29% so với 2,41%). Slope >1 cho thấy dự đoán hơi "rụt rè". Hiệu chuẩn lại (fit trên P) đưa slope về khoảng 1,05; skill không đổi. Với 128 sự kiện, slope chỉ mang tính mô tả (D-32).

**Tại ngưỡng** chọn trên P cho độ nhạy 80%:

| Mô hình | Độ nhạy | Độ đặc hiệu | PPV | Tỷ lệ chuyển xét nghiệm |
|---|---|---|---|---|
| M-AUG | 0,81 | 0,69 | 5,8% | 32% |
| M-PS | 0,80 | 0,69 | 5,6% | 33% |
| **Điểm Bang ≥5** (không có tiền sử gia đình và thể lực) | 0,69 [0,58; 0,80] | 0,66 | 4,5% | 35% |

Điểm Bang có AUROC 0,75 [0,69; 0,81]. Mô hình tìm ra nhiều ca hơn với tỷ lệ chuyển xét nghiệm thấp hơn.

**Net benefit:** ở ngưỡng 2%, mô hình ≈ 0,011–0,012 trên mỗi người được sàng lọc.

## 5. Phân tích phụ (định trước)

| Phân tích | Δ (AUG − PS) [CI] | Nhận xét |
|---|---|---|
| S6 (tiền sử + lối sống; M-AUG không thấy mẫu này khi huấn luyện) | −0,0013 [−0,0056; 0,0030] | Tương đương |
| S7 (thiếu lối sống phụ thuộc học vấn, MAR) | −0,0008 [−0,0027; 0,0012] | Tương đương |
| Nhãn ≥6,4 (172 sự kiện) / ≥6,7 (78 sự kiện) | −0,0003 / +0,0013 | Bền với lệch thiết bị đo HbA1c |
| Loại nhóm borderline | −0,0006 [−0,0024; 0,0011] | Không đổi |
| Nhãn ≥5,7 (mô hình riêng) | −0,0015 [−0,0032; 0,0001] | Tương đương; skill tổng 0,18 |
| Huấn luyện có trọng số khảo sát (LR) | +0,0002 [−0,0033; 0,0036] | Không lợi ích |
| **LightGBM** AUG − PS | **+0,012 [0,008; 0,017]** | Với cây, che khối **tốt hơn** mô hình con |
| LR-AUG − LGB-AUG | +0,006 [−0,003; 0,016] | LR ≥ LightGBM; LightGBM S0 skill 0,022 |

**Nhận xét về LightGBM:** kết quả "che khối tốt hơn" chỉ đúng với LightGBM, và LightGBM vốn kém hơn LR ở cỡ mẫu này. Đây là phát hiện phụ, không thay kết luận chính.

**Phân nhóm** (chỉ nhóm ≥30 sự kiện, mô tả):
- Tuổi ≥65: AUROC 0,70; skill 0,01, rất thấp.
- Tuổi 45–64: AUROC 0,75.
- Nam/nữ: AUROC 0,81/0,82.
- NH White: AUROC 0,82.
- Các nhóm chủng tộc khác và tuổi 20–44 có <30 sự kiện, không báo cáo.

## 6. Giới hạn cần nêu trong bài
1. **Tín hiệu tuyệt đối thấp.** Ở tỷ lệ 2,3%, Brier skill tốt nhất chỉ ≈ 0,035 và PPV ≈ 6%. Công cụ chỉ phù hợp để chọn người đi xét nghiệm HbA1c, không thay xét nghiệm.
2. **Chỉ có một lần kiểm định theo thời gian** với 128 sự kiện. Slope/CITL chỉ mô tả; phân tích phân nhóm rất hạn chế (L không oversample).
3. **Thiếu dữ liệu là mô phỏng.** S1–S6 là thiếu hoàn toàn ngẫu nhiên theo khối; S7 là MAR đơn giản. Cơ chế thiếu thực tế có thể khác.
4. **Thiếu biến ở L.** Không có tiền sử gia đình, ĐTĐ thai kỳ và biến thể lực tương đương, nên hiệu năng thấp hơn các bài dùng các biến này.
5. **Tuning.** Mô hình con M-PS chọn C ở biên trên của lưới (D-45). Learner và δ được chọn sau khi xem dữ liệu phát triển P, trước khi mở L (D-35, D-36).
6. **Bản chất nhãn.** Một lần đo HbA1c không phải chẩn đoán. Kết quả chỉ đại diện dân số Hoa Kỳ, không suy ra cho Việt Nam.

## 7. Câu kết luận đề xuất cho bài báo (nháp)
> Trong kiểm định theo thời gian trên NHANES 2021–2023, một mô hình hồi quy logistic duy nhất được huấn luyện với che khối biến cho độ chính xác tương đương với bộ mô hình con theo mẫu thiếu khi một khối thông tin không xét nghiệm bị thiếu lúc sử dụng (Δ Brier skill −0,0006; CI 95% −0,0023 đến 0,0012; biên tương đương ±0,005). Cả hai đều tốt hơn rõ so với để mô hình tự xử lý giá trị thiếu. Thiếu số đo nhân trắc là nguyên nhân chính làm giảm hiệu năng.
