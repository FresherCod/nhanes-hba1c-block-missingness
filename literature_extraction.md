# Trích xuất tài liệu (T-3) — lần 1

- **Ngày:** 2026-09-24
- **Mức đọc:**
  - **TV-PMC** = toàn văn lấy từ PubMed Central qua công cụ, Claude đọc trực tiếp.
  - **TV-HTML** = toàn văn arXiv HTML, lấy qua công cụ trích xuất, có trích dẫn nguyên văn.
  - **TT** = chỉ tóm tắt.

## Các bài lâm sàng

| Bài | Mức đọc | Cohort / nhãn | Chu kỳ | Chia dữ liệu | Trọng số | Thiếu dữ liệu | Hiệu chuẩn | Ngưỡng |
|---|---|---|---|---|---|---|---|---|
| **Liu và cs. 2025**, JMIR AI, [doi:10.2196/68260](https://doi.org/10.2196/68260) | TV-PMC | ≥20 tuổi, không có thai, DIQ010 = "No". Nhãn: HbA1c ≥6,5 **hoặc** FPG ≥126 **hoặc** OGTT ≥200. **Nhóm không-ĐTĐ bắt buộc có đủ cả 3 xét nghiệm**, nhóm ĐTĐ chỉ cần 1 → chọn mẫu làm tỷ lệ tăng lên 19% | 1999–2020 gộp | Ngẫu nhiên 70/30 | Không | Điền trung bình/mode (không nói fit ở đâu) | Không | **Chọn ngưỡng tối ưu F1 trên chính tập test** |
| **Bang và cs. 2009**, Ann Intern Med, [doi:10.1059/0003-4819-151-11-200912010-00005](https://doi.org/10.1059/0003-4819-151-11-200912010-00005) | TV-PMC | ≥20 tuổi, không có thai, có FPG. Loại người đã chẩn đoán hoặc dùng thuốc. Nhãn: FPG ≥126. Phân tích phụ với HbA1c ≥6,5 (AUC 0,78) | Phát triển 1999–2004 → **kiểm định theo thời gian** 2005–06 | Theo chu kỳ | **Có** (strata, cluster, weight) | Phân loại thiếu → coi như "không có" (quy ước "không biết thì cho 0") | Tỷ lệ theo điểm; không có slope | Điểm ≥5 chọn trên dữ liệu phát triển |
| **Casacchia và cs. 2024**, BMC MIDM, [doi:10.1186/s12911-024-02803-w](https://doi.org/10.1186/s12911-024-02803-w) | TV-PMC | **Không phải mô hình không xét nghiệm**: dùng đường huyết ngẫu nhiên, non-HDL, cholesterol, eGFR. Nhãn HbA1c ≥5,7. Phát triển trên EHR | Kiểm định ngoài trên NHANES P (n = 2.348) | Khác miền | Trọng số lúc đói đã chuẩn hóa | Complete-case | Intercept, slope, ICI, Brier; hiệu chuẩn lại bằng logistic | — |
| **Beyond the Blood Draw 2026**, arXiv:2606.16056 | TV-HTML | ≥18 tuổi, không có thai. Nhãn: HbA1c ≥5,7 **hoặc DIQ010 = 1** (gồm cả người đã chẩn đoán). Có dùng tiền sử gia đình, thuốc hạ áp, cholesterol cao | P + L **gộp** | Ngẫu nhiên 80:20 | Không | MICE fit trên train | Đường cong, Brier, DCA | Youden (không nói chọn trên tập nào) |
| **MEDWACS 2026** (Yoo, Maggiore, Jolliet), J Clin Epidemiol, [doi:10.1016/j.jclinepi.2026.112266](https://doi.org/10.1016/j.jclinepi.2026.112266) | **TV-PDF** (Vincent cung cấp) | Nhãn: FPG ≥100 **hoặc** HbA1c ≥5,7. Dân số phát triển là người có FPG (loại người đang điều trị ĐTĐ). 7 biến: tuổi, giới, eo, HA tâm thu, chiều dài đùi, vòng cánh tay, BMI. Tác giả ghi "không chuẩn bị protocol" | Phát triển 1988–2018 (n = 17.458) → kiểm định ngoài NHANES 2021–2023 (n = 3.043, tỷ lệ 63%) và KNHANES 2023 | Ngẫu nhiên 7:3 + ngoài theo thời gian/quốc gia | **Không** dùng khi huấn luyện/đánh giá | Complete-case (loại biến thiếu ≥20%); ở 2021–2023 điền chiều dài đùi bằng hồi quy | Đường cong + Brier 0,183; không có slope/intercept | Youden theo 2 nhóm tuổi, trên CV |
| **Matabuena và cs. 2024/25**, arXiv:2403.19752 | TV-HTML | Nhãn gồm cả người đã chẩn đoán. Có biến xét nghiệm (cholesterol, triglyceride, HbA1c ở các mô hình lớn) | 2011–2014 | Ngẫu nhiên 60/20/20 | **Loss có trọng số** | Không nêu | Không | — |
| Hutchison và cs. 2025, medRxiv 10.1101/2025.02.10.25321897 | TV-PDF | Mô hình **có xét nghiệm** (FPG, insulin, lipid, men gan); n = 13.800 có HbA1c + OGTT | Nhiều chu kỳ đến 2015–2016 | Theo chu kỳ | Có dùng biến trọng số | Loại biến thiếu >12% | — | — |
| Xu và cs. 2026, J Diabetes Res, [doi:10.1155/jdr/4525736](https://doi.org/10.1155/jdr/4525736) | TT | T2DM, chỉ dùng L | L | Ngẫu nhiên | ? | MI Monte Carlo | Không nêu | — |

## Các bài phương pháp về thiếu dữ liệu lúc dự đoán

| Bài | Mức đọc | Nội dung liên quan |
|---|---|---|
| Mercaldo & Blume 2020, *Missing data and prediction: the pattern submodel*, Biostatistics ([PMC7868046](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7868046/)) | TT (qua kết quả tìm kiếm) | Mô hình con theo từng mẫu thiếu; giữ được độ chính xác dự đoán cả khi thiếu không ngẫu nhiên (MNAR); thường tốt hơn MI và imputation → **đối chứng mạnh bắt buộc phải có** |
| Catoire, Genuer, Proust-Lima 2026, arXiv:2603.17599 | TT | Thiếu ở cả phát triển, kiểm định và triển khai; ứng dụng trong chấn thương, không phải ĐTĐ |
| Front AI 2026, PMID 42630411, [doi:10.3389/frai.2026.1898153](https://doi.org/10.3389/frai.2026.1898153) | TT | "Dynamic routing" sang mô hình con khi có HbA1c/glucose, gần ý tưởng pattern submodel. Có biến xét nghiệm, dữ liệu đa nguồn, không phải người chưa chẩn đoán → cần trích dẫn khi bàn về mô hình con theo dữ liệu sẵn có |

## Hệ quả cho tính mới (G4)

| Khác biệt đề xuất ở v0.2 | Đã có bài làm? | Đánh giá |
|---|---|---|
| Chỉ người chưa chẩn đoán, HbA1c ≥6,5 | Liu 2025 (nhãn gộp), Bang 2009 (FPG, có phân tích phụ HbA1c) | **Không mới** |
| Kiểm định theo thời gian sang 2021–2023 | **MEDWACS đã làm** (nhãn khác: tiền ĐTĐ + ĐTĐ). Bang làm theo thời gian ở các chu kỳ cũ | **Không mới**; chỉ khác ở nhãn |
| (Xác nhận toàn văn MEDWACS) Có so sánh chiến lược thiếu khối? | **Không** — complete-case khi phát triển, điền 1 biến khi kiểm định | G4 đạt (D-40) |
| Đánh giá có trọng số theo thiết kế | Bang, Casacchia | **Không mới** |
| Thiếu cả khối lúc triển khai: augmentation vs pattern submodel vs NaN tự nhiên, cho sàng lọc ĐTĐ không xét nghiệm | **Không tìm thấy** trong các nguồn đã tìm | **Đây là đóng góp duy nhất còn đứng được** → câu hỏi chính của v0.2 vẫn đúng hướng |

**Hệ quả thiết kế (đề xuất D-30):** vì pattern submodel là phương pháp chuẩn đã biết, so M-AUG với LightGBM không che (M-BASE) gần như chắc chắn thắng mà không cho nhiều thông tin. So sánh chính nên là **M-AUG vs pattern submodel**.

## Sửa lỗi các báo cáo AI ([TĐ]/[KT]/[LR]), đã xác minh bằng toàn văn

- Casacchia: **không** phải "8 biến phi xét nghiệm" — mô hình có đường huyết, lipid, eGFR.
- Liu: có mô tả "gộp chu kỳ, chia ngẫu nhiên, không trọng số, không hiệu chuẩn" là đúng; nhưng các báo cáo **bỏ sót** hai điểm: chọn ngưỡng trên tập test, và nhóm không-ĐTĐ bắt buộc có đủ 3 xét nghiệm.
- Bang: nhãn là FPG, không phải HbA1c. Không dùng ĐTĐ thai kỳ. Thể lực định nghĩa bằng câu "so với người cùng tuổi".
- Không báo cáo AI nào nhắc đến Beyond the Blood Draw hoặc MEDWACS — hai bài gần nhất.
