# Tích hợp A4 — đối chiếu các đầu ra AI với nguồn gốc

Ngày: 2026-09-24 · Người tích hợp: Claude (theo yêu cầu của Vincent) · Trạng thái: **nháp để duyệt**

## Ký hiệu nguồn

| Mã | Tài liệu | Bản chất |
|---|---|---|
| [TĐ] | `BÁO CÁO THẨM ĐỊNH BẰNG CHỨNG VÀ ĐÁNH GIÁ TÍNH MỚI…docx` | Đầu ra AI (Gemini/NotebookLM) — **chưa coi là sự thật** |
| [KT] | `Kiểm Tra Tính Mới NHANES.docx` | Đầu ra AI — chưa coi là sự thật |
| [LR] | `NHANES Diabetes Screening Literature Review.docx` | Đầu ra AI — chưa coi là sự thật |
| [CL] | Phản biện phương pháp của Claude (hội thoại 2026-09-24) | Đầu ra AI — chưa coi là sự thật |
| [KH] | Kế hoạch do Vincent dán (chỉ có mục 8–9 và gói D2; **không có mục 1–7**) | Kế hoạch |
| [NG-x] | Trang nguồn gốc Claude đã mở ngày 2026-09-24 (liệt kê dưới) | Nguồn gốc, **đọc qua công cụ trích xuất tự động** → mức tin cậy trung bình, phải khớp lại bằng audit dữ liệu hoặc đọc tay |

Nguồn gốc đã mở:
- [NG-GHB_L] https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm
- [NG-P_GHB] https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_GHB.htm
- [NG-DIQ_L] https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm
- [NG-DEMO_L] https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm
- [NG-PAQ_L] https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/PAQ_L.htm
- [NG-P_PAQ] https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_PAQ.htm
- [NG-L] https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- [NG-NIDDK] https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test
- [NG-BBD] arXiv:2606.16056 "Beyond the Blood Draw…" (trang abs + bản HTML)
- [NG-MAT] arXiv:2403.19752 Matabuena et al. (chỉ trang abs)

Chưa mở: Health and Technology (phí xuất bản), Colab FAQ — không ảnh hưởng thiết kế.

## Bảng tích hợp

| # | Chủ đề | Điểm thống nhất | Mâu thuẫn | Bằng chứng gốc | Cách kiểm chứng | Quyết định đề nghị |
|---|---|---|---|---|---|---|
| 1 | Phạm vi | [LR], [CL], mô tả của Vincent: một kết cục, chỉ biến không xét nghiệm | [TĐ]/[KT]: đa bệnh ĐTĐ+THA+CVD, Tầng 2 có glucose/lipid, định tuyến EVOI | Không cần nguồn; là lựa chọn của đề tài | — | **Chốt**: một kết cục HbA1c, không Tầng 2, không đa nhiệm (D-01) |
| 2 | Ngưỡng nhãn | [KT] nêu 6,5% (ngữ cảnh chẩn đoán); [CL] đề nghị 6,5% | [LR]: ảnh công thức "HbA1c ≥" **trống giá trị** | [NG-NIDDK]: <5,7 bình thường; 5,7–6,4 tiền ĐTĐ; ≥6,5 ĐTĐ; **chẩn đoán cần xét nghiệm lặp lại** | Đã khớp nguồn | **Chốt**: nhãn chính HbA1c ≥6,5%, gọi là "HbA1c đạt ngưỡng ĐTĐ", không gọi "ĐTĐ chưa chẩn đoán" (D-02). Nhãn dự phòng 5,7% có điều kiện kích hoạt (D-03) |
| 3 | "Chưa chẩn đoán" | [CL]: loại DIQ010=1, người dùng insulin/thuốc | Không tài liệu AI nào định nghĩa | [NG-DIQ_L]: DIQ010 ở L: 1=1.081, 2=10.371, 3=284, 9=4; **DIQ050 (insulin) chỉ hỏi người đã chẩn đoán** | Audit: bảng chéo DIQ010×DIQ050×DIQ070 ở P và L | **Chốt một phần**: loại DIQ010∈{1,7,9}. DIQ010=3 (borderline): **chưa chốt**, giữ ở phân tích chính và làm phân tích độ nhạy (D-04). Không dùng DIQ050 để xác định người chưa chẩn đoán |
| 4 | Trọng số cho HbA1c | [TĐ], [KT], [CL]: dùng trọng số MEC | **Mâu thuẫn với nguồn gốc** ở chu kỳ L | [NG-GHB_L]: dùng **WTPH2YR** (trọng số lấy máu; 95% người ≥18 có mẫu máu). [NG-P_GHB]: dùng trọng số trong file DEMO của tệp gộp (= WTMECPRP, cần xác nhận) | Audit: kiểm tra biến có tồn tại, số trọng số bằng 0, tổng trọng số | **Chốt có điều kiện**: P dùng WTMECPRP, L dùng WTPH2YR, cả hai kiểm lại trong audit (D-05). Sửa R-03 của [TĐ]/[KT] |
| 5 | Đổi phương pháp đo HbA1c | [CL] nêu rủi ro; tài liệu AI không nhắc | — | [NG-GHB_L]: L dùng Tosoh G8 rồi Bio-Rad D-100; G8 cao hơn trung bình 2,3%, NCHS **không điều chỉnh**. [NG-P_GHB]: sai số giữa thiết bị phụ 0,5% | 2,3% của 6,5 ≈ 0,15 điểm phần trăm, đủ để dịch nhãn gần ngưỡng. Audit: xem có biến chỉ thiết bị không; phân phối LBXGH quanh 6,3–6,7 | **Chưa chốt**: không điều chỉnh ở phân tích chính (theo NCHS); thêm phân tích độ nhạy ngưỡng ±0,15 ở L (D-06) |
| 6 | Sơ đồ chu kỳ | [KT], [CL]: chu kỳ phải tách biệt, không trộn | [LR]: phát triển 1999–2014 → kiểm định 2015–2020; [KT]: P → L | [NG-DEMO_L]: NCHS khuyến cáo thận trọng khi gộp L với chu kỳ trước (gián đoạn 15 tháng); L không oversample theo chủng tộc/thu nhập. [NG-PAQ_L]/[NG-P_PAQ]: L bỏ các câu GPAQ, thay bằng câu LTPA mới; PAD680 có ở cả hai | Audit: số sự kiện L | **Đề nghị**: phát triển trên P, kiểm định theo thời gian trên L (D-07); **chưa chốt** cho đến khi audit đạt cổng G2. Phương án 1999–2014 bị gác lại vì phải hài hòa nhiều bảng hỏi hơn |
| 7 | "Survey-aware GB" là tính mới | [TĐ], [KT] coi là đóng góp cốt lõi | [CL]: chỉ là `sample_weight`; [LR] tự ghi "không tăng thời gian tính toán" | [NG-MAT]: Matabuena và cs. (2024, sửa 2025) đã đưa trọng số khảo sát vào huấn luyện mạng nơ-ron và lượng hóa bất định cho sàng lọc ĐTĐ trên NHANES 2011–2014 | Đọc toàn văn [NG-MAT] | **Chốt**: bỏ khỏi danh sách đóng góp. Huấn luyện có hay không có trọng số chỉ là yếu tố phụ (D-08) |
| 8 | Bài gần nhất | [CL]: Liu 2025, Bang 2009, Choi 2023, Casacchia 2024 | [KT]: CardioMeta | [NG-BBD] (trích xuất tự động): NHANES 2017–2023 **gộp**, n=14.352, nhãn = HbA1c ≥5,7% **hoặc ĐTĐ đã chẩn đoán** (tỷ lệ 42,5%), 29 biến không xâm lấn, MICE fit trên train, chia ngẫu nhiên 80:20 + CV 5 fold, **không trọng số**, có Brier, đường cong hiệu chuẩn, DCA, so với ADA và FINDRISC, ngưỡng Youden. **Không tài liệu AI nào liệt kê bài này** | Vincent đọc tay toàn văn [NG-BBD] | **Chốt tạm**: [NG-BBD] là bài so sánh chính cho tính mới. Khác biệt cần chứng minh: (a) chỉ người chưa chẩn đoán, (b) P→L theo thời gian, (c) đánh giá có trọng số theo thiết kế, (d) thiếu theo khối (D-09) |
| 9 | Tính mới của thiếu theo khối | [LR], [CL] coi là câu hỏi chính | [LR] khẳng định "chưa từng" mà không có log tìm kiếm | Không có | Nhiệm vụ T-2: tìm có hệ thống và lưu log | **Chưa chốt** câu khẳng định tính mới; câu hỏi chính giữ nguyên (D-10) |
| 10 | Xử lý thiếu | [LR]: LightGBM xử lý NaN + masking | [TĐ]/[KT]: HGB-MICE; [CL]: nói rõ fit ở đâu | [NG-BBD] dùng MICE fit trên train | — | **Chốt**: không MICE ở phân tích chính. LightGBM dùng NaN tự nhiên; LR baseline dùng trung vị/mode fit trên train + biến chỉ báo thiếu (D-11) |
| 11 | Hiệu chuẩn lại | [TĐ]/[KT]: isotonic có trọng số | [CL]: logistic, chỉ fit trên dữ liệu phát triển | — | — | **Chốt**: hiệu chuẩn lại bằng logistic trên dự đoán OOF của P. Cập nhật trên L chỉ là phân tích phụ, chia theo PSU (D-12) |
| 12 | Chia fold, bất định | [TĐ]/[KT]/[CL]: giữ cụm PSU | [TĐ]/[KT] R-02 viết gộp cả strata vào một fold | [NG-DEMO_L]: L có 15 strata × 2 PSU (30 PSU) → bậc tự do thiết kế ≈15 | Audit: đếm strata/PSU ở P | **Chốt**: CV trên P theo nhóm (SDMVSTRA, SDMVPSU); CI trên L bằng jackknife JK2 theo PSU, t với 15 bậc tự do (D-13) |
| 13 | Số sự kiện | [CL] yêu cầu; tài liệu AI không có | — | [NG-GHB_L]: 6.715 người có HbA1c ở L (mọi tuổi ≥12). [NG-P_GHB]: 9.737 ở P | Audit | **Cổng G2** (D-03) |
| 14 | Đối chứng | [CL]: ADA, LR, LightGBM không augmentation, mô hình con theo mẫu thiếu | [LR]: chỉ LR, LightGBM, MLP | [NG-BBD] so với ADA và FINDRISC | Audit: có dựng được biến ADA ở cả P và L không (thể lực!) | **Chốt**: 4 đối chứng; ánh xạ điểm ADA **chưa chốt** (D-14). Bỏ MLP |
| 15 | Ngưỡng | [CL]: định trước trên dữ liệu phát triển | [KT]: để mở; [NG-BBD] dùng Youden | — | — | **Chốt**: ngưỡng chọn trên OOF của P ở độ nhạy 80% (giá trị **chưa chốt**, cần lý do lâm sàng), rồi áp nguyên cho L (D-15) |
| 16 | Công bằng | [KT], [CL] | — | [NG-DEMO_L]: L không oversample → phân nhóm kém chính xác. [NG-NIDDK]: biến thể hemoglobin làm sai HbA1c ở một số nhóm tổ tiên | Audit: số sự kiện theo nhóm | **Chốt**: chỉ mô tả; nhóm có <30 sự kiện ở L thì không báo chỉ số (D-16) |
| 17 | Biến rò rỉ / gián tiếp là xét nghiệm | [CL] | [KT] loại huyết áp đo vì nhãn THA | [NG-DIQ_L]: có DIQ160 (tiền ĐTĐ), DIQ180 (thử máu 3 năm qua) | — | **Chốt**: loại DIQ160, DIQ180, BPQ080, thuốc hạ mỡ; **giữ** huyết áp đo, là khối có thể che (D-17) |
| 18 | Tuổi, thai kỳ | — | [TĐ]: >18 | [NG-DEMO_L]: RIDEXPRG chỉ công bố cho 20–44 tuổi; tuổi top-code ở 80. [NG-NIDDK]: không dùng A1C cho thai kỳ | — | **Chốt**: tuổi ≥20; loại RIDEXPRG=1 (D-18) |
| 19 | Thể lực | [TĐ] đặt câu hỏi PAD680 | — | PAD680 có ở P và L, nhưng L có ghi chú probe thay đổi từ 2011. GPAQ không có ở L | — | **Chưa chốt** quy tắc hài hòa: PAD680 + biến "có hoạt động thể lực giải trí" dựng từ PAQ650/665 (P) và PAD790/810 (L) (D-19) |
| 20 | Trích dẫn trong ma trận AI | [CL] chỉ ra nhiều định danh không khớp | — | Chưa kiểm | Nhiệm vụ T-3 | Không trích bài nào từ [TĐ]/[KT]/[LR] vào bản thảo khi chưa mở bản gốc (D-20) |
| 21 | Ngân sách, xuất bản, Colab | [LR], [KH] | — | Chưa mở | — | Ngoài phạm vi phương pháp; không xử lý ở đây |

## Nhận xét AI chưa được kiểm chứng (không dùng làm căn cứ)
- Mọi con số hiệu năng của CardioMeta, Pall, SaML, Rogers & Wang, Dinh, Liu trong [TĐ]/[KT]/[LR].
- "Trần AUROC 0,78–0,83", "mọi AUROC >0,90 là rò rỉ" ([LR]).
- "Gradient variance spikes" khi đưa trọng số vào GBDT ([TĐ] — chính tài liệu gắn nhãn là suy luận).
- "Mất 20–50% cỡ mẫu nếu dùng complete-case" ([LR]).
- Nội dung chi tiết của [NG-BBD] và [NG-MAT] ở trên đến từ công cụ trích xuất, **chưa đọc tay**.
