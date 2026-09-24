# Search log (T-2) — lần 1

- **Người tìm:** Claude, thay Vincent
- **Ngày:** 2026-09-24
- **Giới hạn:** chỉ sàng lọc qua tiêu đề và tóm tắt. Toàn văn chỉ đọc cho các bài đưa vào `literature_extraction.md`. Chưa tìm Google Scholar, Scopus, IEEE, medRxiv API (bị chặn 403).
- **Kết luận chỉ có giá trị ở mức "không tìm thấy trong các nguồn đã tìm"**, không phải "chưa từng có".

## Truy vấn

| # | Nguồn | Truy vấn | Kết quả | Liên quan |
|---|---|---|---|---|
| Q1 | PubMed (qua MCP) | `NHANES[tiab] AND (undiagnosed diabetes[tiab] OR HbA1c[tiab] OR dysglycemia[tiab]) AND (machine learning[tiab] OR prediction model[tiab] OR risk score[tiab]) AND (temporal[tiab] OR external validation[tiab] OR calibration[tiab])` | 21 | 2: PMID 41950976 (MEDWACS), 21193764 (JADA 2011, hướng dẫn cho nha sĩ, CART, NHANES III → 2003–04, nhãn FPG) |
| Q2 | PubMed | `(undiagnosed diabetes OR HbA1c OR dysglycemia OR diabetes screening) AND (missing data OR missingness OR incomplete predictors OR missing predictors) AND (prediction model OR machine learning) AND (NHANES OR survey)` | 73 PMID; công cụ trả metadata cho **40/73** (33 PMID không trả về, chưa sàng lọc) | Sàng lọc tiêu đề + tóm tắt 40 bài: 2 liên quan một phần — PMID 42630411 (Front AI 2026, [doi:10.3389/frai.2026.1898153](https://doi.org/10.3389/frai.2026.1898153): định tuyến sang mô hình con theo dữ liệu sẵn có, **có** biến xét nghiệm, dữ liệu đa nguồn, không phải NHANES người chưa chẩn đoán, không theo thời gian); PMID 29027512 (2017, [doi:10.1177/1460458217733288](https://doi.org/10.1177/1460458217733288): thiếu dữ liệu EHR làm hỏng mô hình nguy cơ ĐTĐ chưa chẩn đoán, mô phỏng thiếu). Không bài nào so sánh augmentation với pattern submodel trong sàng lọc ĐTĐ không xét nghiệm |
| Q3 | PubMed | `NHANES AND (2021-2023 OR post-pandemic) AND diabetes AND (machine learning OR prediction)` | 7 | 2: 41950976 (MEDWACS), 41934166 (Xu 2026, chỉ dùng L, có MI + ADASYN, chia ngẫu nhiên) |
| Q4 | arXiv API | `all:NHANES AND (all:diabetes OR all:HbA1c) AND (all:missing OR all:missingness OR all:temporal OR all:calibration)` | 5 | 2607.15721 (CardioMeta), 2607.16253 (Pall) — đã biết; không có bài về thiếu theo khối trong sàng lọc ĐTĐ |
| Q5 | Web search | `NHANES undiagnosed diabetes prediction missing predictors "block missingness" OR "pattern submodel" non-laboratory` | 9 | Phương pháp: Mercaldo & Blume 2020 (pattern submodel, Biostatistics, PMC7868046); Catoire và cs. 2026 (arXiv:2603.17599, thiếu lúc triển khai, dữ liệu chấn thương); tổng quan về thiếu dữ liệu trong mô hình ĐTĐ chưa chẩn đoán (PMC4380106) |
| Q6 | Web search | `medRxiv 2026 NHANES 2021-2023 non-laboratory diabetes risk model temporal validation pre-pandemic` | 9 | MEDWACS; Beyond the Blood Draw; medRxiv 10.1101/2025.02.10.25321897 (403, **chưa đọc được**); tổng quan công cụ không xét nghiệm cho tiền ĐTĐ (PMC10093270) |

## Việc còn lại
- Sàng lọc 33 PMID còn lại của Q2 (metadata không trả về).
- Tìm Google Scholar với cụm "missing at deployment" / "feature unavailability" + "diabetes risk".
- Lấy PDF của MEDWACS và medRxiv 2025.02.10.25321897.
- Đọc hai tổng quan PMC4380106 và PMC10093270 để lấy danh sách bài cũ hơn.
